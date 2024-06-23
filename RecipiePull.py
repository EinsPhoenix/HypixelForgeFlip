import os
import git
import shutil

batch_script = "delete.bat"
repo_url = 'https://github.com/NotEnoughUpdates/NotEnoughUpdates-REPO.git'
clone_path = './NotEnoughUpdates-REPO'
commit_hash = 'f73d9d055f133e93ccd7af162be74c529c8b7bfa'

folder_to_copy = 'items'
destination_path = './downloaded_items'

def delete_files_in_folder(folder_path):
    try:
        if not os.path.isdir(folder_path):
            raise ValueError(f"{folder_path} ist kein gültiges Verzeichnis.")

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Datei {file_path} wurde erfolgreich gelöscht.")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Verzeichnis {file_path} wurde erfolgreich gelöscht.")
            except Exception as e:
                print(f"Fehler beim Löschen von {file_path}: {e}")
        shutil.rmtree(folder_path)
        print(f"Alle Dateien in {folder_path} wurden erfolgreich gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen der Dateien in {folder_path}: {e}")

def CloneRecipies():
    if not os.path.exists(clone_path):
        git.Repo.clone_from(repo_url, clone_path)

    repo = git.Repo(clone_path)
    repo.git.checkout(commit_hash)

    source_path = os.path.join(clone_path, folder_to_copy)

    if os.path.exists(source_path):
        if os.path.exists(destination_path):
            shutil.rmtree(destination_path)
        shutil.copytree(source_path, destination_path)
        print(f"Der Ordner {folder_to_copy} wurde erfolgreich nach {destination_path} kopiert.")
    else:
        print(f"Der Ordner {folder_to_copy} existiert nicht im Repository.")
    shutil.move("./NotEnoughUpdates-REPO/constants/reforges.json", "./DataAPI")
    os.system(batch_script)
    delete_files_in_folder("./NotEnoughUpdates-REPO")



def update_recipes():
    os.system(batch_script)
    delete_files_in_folder("./downloaded_items")
    delete_files_in_folder("./NotEnoughUpdates-REPO")
    CloneRecipies()


