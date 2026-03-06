import os
import sys
import threading
import win32serviceutil
import win32service
import win32event
import servicemanager
from multiprocessing.connection import Listener

class NTFSSearchService(win32serviceutil.ServiceFramework):
    _svc_name_ = "NTFSSearchEngine"
    _svc_display_name_ = "NTFS Fast Search Service"
    _svc_description_ = "Provides lightning-fast local file search capabilities via USN Journal."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Create an event to listen for the Stop command from Windows
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True

    def SvcStop(self):
        # Tell Windows we are shutting down
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # Tell Windows we have started successfully
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        sys.path.append(script_dir)

        import ntfs_indexer

        engine = ntfs_indexer.NTFSSearchEngine()
        index_file = os.path.join(script_dir, "index.bin")

        # Load or Build Index
        if os.path.exists(index_file):
            engine.load_index(index_file)
        else:
            engine.build_index(["C:"])
            engine.save_index(index_file)

        # --- THE FIX: Put the blocking server in a background daemon thread ---
        def server_worker():
            address = ('127.0.0.1', 27015)
            listener = Listener(address, authkey=b'secret_ntfs_key')
            
            while self.is_running:
                try:
                    with listener.accept() as conn:
                        query = conn.recv()
                        if query:
                            results = engine.search(query)
                            conn.send(results)
                except Exception:
                    pass

        # Start the listener thread
        server_thread = threading.Thread(target=server_worker)
        server_thread.daemon = True # Thread dies instantly when service stops
        server_thread.start()

        # The main Windows Service thread waits here patiently until Windows sends a stop signal
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(NTFSSearchService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(NTFSSearchService)