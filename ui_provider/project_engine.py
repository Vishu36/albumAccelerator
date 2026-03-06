import sqlite3
import os
import io
from PySide6.QtCore import QObject, Signal
import sqlite3
import os
import PIL.Image as PIL_Image


class project_engine1(QObject):
    onProjectLoaded = Signal()

    def __init__(self):
        super().__init__()
        self.projectFile: str = None
        self.connection = None
        self.cursor = None

    def load(self, projectFile):
        self.projectFile = projectFile
        self.connection = sqlite3.connect(projectFile)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS Folders
                            (
                                folderID
                                INTEGER
                                PRIMARY
                                KEY,
                                folderName
                                TEXT,
                                folderPath
                                TEXT
                                UNIQUE
                            )
                            """)
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS Images
                            (
                                folder
                                TEXT,
                                name
                                TEXT,
                                isUsed
                                INT,
                                isHighlight
                                INT,
                                orientation
                                TEXT,
                                thumb
                                BLOB,
                                Path
                                TEXT
                                UNIQUE
                            )
                            """)

        self.connection.commit()
        self.onProjectLoaded.emit()

    def getAllFolder(self):
        self.cursor.execute("SELECT * FROM Folders")
        return self.cursor.fetchall()

    def addFolder(self, folderPath):
        folderName = os.path.basename(os.path.normpath(folderPath))
        try:
            self.cursor.execute(
                "INSERT INTO Folders (folderPath, folderName) VALUES (?, ?)",
                (folderPath, folderName)
            )
            self.connection.commit()
            print(f"Successfully added: {folderName}")

        except:
            ...

    def removeFolder(self, folderPath):
        self.cursor.execute("DELETE FROM Folders WHERE folderPath = ?", (folderPath,))
        self.connection.commit()
        print(f"Deleted folder with path: {folderPath}")

    def addImages(self, images: list[tuple[str, str, int, int, str, str, bytes]]):
        self.cursor.executemany(
            """
            INSERT
            OR IGNORE INTO Images
            (folder, name, isUsed, isHighlight, orientation, thumb, Path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            images
        )
        self.connection.commit()


class project_engine(QObject):
    onProjectLoaded = Signal()

    def __init__(self):
        super().__init__()
        self.projectFile = None
        self.connection = None
        self.cursor = None
        self.supportedExt = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.psd')

    def load(self, projectFile):
        self.projectFile = projectFile
        self.connection = sqlite3.connect(projectFile, check_same_thread=False)
        self.cursor = self.connection.cursor()

        # Create Tables
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS Folders
                            (
                                folderID
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                folderName
                                TEXT,
                                folderPath
                                TEXT
                                UNIQUE
                            )""")
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS Images
                            (
                                imageID
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                imageName
                                TEXT,
                                imagePath
                                TEXT
                                UNIQUE,
                                isUsed
                                BOOLEAN
                                DEFAULT
                                0,
                                isHighlight
                                BOOLEAN
                                DEFAULT
                                0,
                                isCached
                                BOOLEAN
                                DEFAULT
                                0,
                                orientation
                                TEXT,
                                thumb
                                BLOB
                            )""")
        self.connection.commit()
        self.onProjectLoaded.emit()

    def addFolder(self, folderPath):
        folderName = os.path.basename(os.path.normpath(folderPath))
        try:
            self.cursor.execute(
                "INSERT INTO Folders (folderPath, folderName) VALUES (?, ?)",
                (folderPath, folderName)
            )
            self.connection.commit()
            self.scanFolder(folderPath)
            print(f"Successfully added: {folderName}")

        except:
            ...

    def removeFolder(self, folderPath):
        # Convert any Windows backslashes (\) to Qt/Web forward slashes (/)
        # so it perfectly matches the strings already saved in your database.
        db_formatted_path = folderPath.replace('\\', '/')

        # Execute the delete query
        self.cursor.execute("DELETE FROM Folders WHERE folderPath = ?", (db_formatted_path,))
        self.connection.commit()

        # Check if it worked
        if self.cursor.rowcount == 0:
            print(f"WARNING: Still couldn't find an exact match for: {db_formatted_path}")
        else:
            print(f"SUCCESS: Deleted {self.cursor.rowcount} folder(s) from database.")

    def getAllFolder(self):
        """
        Retrieves all registered folders from the database.
        Returns a list of dictionaries.
        """
        try:
            self.cursor.execute("SELECT folderID, folderName, folderPath FROM Folders")
            rows = self.cursor.fetchall()

            folders = []
            for r in rows:
                folders.append({
                    "id": r[0],
                    "name": r[1],
                    "path": os.path.normpath(r[2])  # Keep paths consistent
                })
            return folders
        except sqlite3.Error as e:
            print(f"Database error in getAllFolder: {e}")
            return []

    def scanFolder(self, folderPath):
        folderPath = os.path.normpath(folderPath)  # Fix slash glitches
        if not os.path.isdir(folderPath):
            print(f"Directory not found: {folderPath}")
            return

        # Get existing paths once to prevent re-processing
        self.cursor.execute("SELECT imagePath FROM Images")
        existing_paths = {row[0] for row in self.cursor.fetchall()}

        new_images = []
        all_files = [f for f in os.listdir(folderPath) if f.lower().endswith(self.supportedExt)]

        for filename in all_files:
            full_path = os.path.normpath(os.path.join(folderPath, filename))

            # This ensures we NEVER overwrite or re-process existing data
            if full_path in existing_paths:
                continue

            try:
                with PIL_Image.open(full_path) as img:
                    orientation = "H" if img.width >= img.height else "V"

                # (imageName, imagePath, isUsed, isHighlight, isCached, orientation, thumb)
                new_images.append((filename, full_path, 0, 0, 0, orientation, b""))
            except Exception as e:
                print(f"Skipping {filename}: {e}")

        if new_images:
            self.cursor.executemany("""
                                    INSERT
                                    OR IGNORE INTO Images 
                (imageName, imagePath, isUsed, isHighlight, isCached, orientation, thumb)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, new_images)
            self.connection.commit()
            print(f"Done! Added {len(new_images)} new images.")

    def getImagesFromFolder(self, folderPath):
        folderPath = os.path.normpath(folderPath)
        # We search for paths starting with this folder path
        search_pattern = f"{folderPath}{os.sep}%"

        self.cursor.execute("""
                            SELECT imageID,
                                   imageName,
                                   imagePath,
                                   isUsed,
                                   isHighlight,
                                   isCached,
                                   orientation,
                                   thumb
                            FROM Images
                            WHERE imagePath LIKE ?
                            """, (search_pattern,))

        return [
            {"id": r[0], "name": r[1], "path": r[2], "used": bool(r[3]), "highlight": bool(r[4]), "icached": r[5],
             "orientation": r[6], "thumb": r[7], }
            for r in self.cursor.fetchall()
        ]

    def toggleImageHighlight(self, imagePath):
        imagePath = os.path.normpath(imagePath)
        # Atomic toggle directly in SQL - no need to SELECT first
        self.cursor.execute("""
                            UPDATE Images
                            SET isHighlight = NOT isHighlight
                            WHERE imagePath = ?
                            """, (imagePath,))
        self.connection.commit()
        print(f"Highlight toggled for: {imagePath}")

    def toggleImageUsed(self, imagePath):
        imagePath = os.path.normpath(imagePath)
        # Atomic toggle directly in SQL - no need to SELECT first
        self.cursor.execute("""
                            UPDATE Images
                            SET isUsed = NOT isUsed
                            WHERE imagePath = ?
                            """, (imagePath,))
        self.connection.commit()
        print(f"Used toggled for: {imagePath}")

    # --- ADD THESE METHODS TO project_engine CLASS ---

    def setImagesUsed(self, imagePaths: list, state: int):
        # state: 1 for Used, 0 for Unused
        normalized_paths = [(state, os.path.normpath(p)) for p in imagePaths]
        self.cursor.executemany("""
                                UPDATE Images
                                SET isUsed = ?
                                WHERE imagePath = ?
                                """, normalized_paths)
        self.connection.commit()
        print(f"Updated 'isUsed' state for {len(imagePaths)} images.")

    def toggleImagesHighlight(self, imagePaths: list):
        normalized_paths = [(os.path.normpath(p),) for p in imagePaths]
        self.cursor.executemany("""
                                UPDATE Images
                                SET isHighlight = NOT isHighlight
                                WHERE imagePath = ?
                                """, normalized_paths)
        self.connection.commit()
        print(f"Toggled highlight for {len(imagePaths)} images.")

    def removeImages(self, imagePaths: list):
        normalized_paths = [(os.path.normpath(p),) for p in imagePaths]
        self.cursor.executemany("""
                                DELETE
                                FROM Images
                                WHERE imagePath = ?
                                """, normalized_paths)
        self.connection.commit()
        print(f"Removed {len(imagePaths)} images from database.")

    def rotateRealImages(self, imagePaths: list, angle: int):
        # angle: 90 for Anti-Clockwise, -90 for Clockwise
        for path in imagePaths:
            full_path = os.path.normpath(path)
            try:
                # expand=True prevents rectangular images from clipping their corners
                with PIL_Image.open(full_path) as img:
                    rotated = img.rotate(angle, expand=True)
                    rotated.save(full_path)
            except Exception as e:
                print(f"Failed to rotate {full_path}: {e}")
