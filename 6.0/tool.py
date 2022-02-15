import os
import shutil
import zipfile


class tool:
    def __init__(self):
        self.zip_file = None

    def move_file(self, old_path, new_path):
        if os.path.isdir(old_path):
            filelist = os.listdir(old_path)
            for file in filelist:
                if os.path.isdir(old_path + file):
                    self.move_file(old_path + file, new_path)
                else:
                    src = os.path.join(old_path, file)
                    dst = os.path.join(new_path)
                    shutil.move(src, dst)
        else:
            src = os.path.join(old_path)
            dst = os.path.join(new_path)
            shutil.move(src, dst)

    def create_zip(self, target_path, target_name):
        self.zip_file = zipfile.ZipFile(target_name, 'w')
        self.get_zip(target_path)
        self.zip_file.close()

    def get_zip(self, input_path):
        files = os.listdir(input_path)
        for file in files:
            filePath = input_path + '/' + file
            if os.path.isdir(filePath):
                self.get_zip(filePath)
            else:
                self.zip_file.write(filePath, file, zipfile.ZIP_DEFLATED)
