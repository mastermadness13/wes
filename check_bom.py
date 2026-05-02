import os

def find_files_with_bom(directory):
    """
    Scans a directory for files containing the UTF-8 BOM signature.
    """
    # The UTF-8 BOM signature in bytes
    BOM_SIGNATURE = b'\xef\xbb\xbf'
    files_with_bom = []

    # Extensions commonly associated with source code in your project
    target_extensions = ('.py', '.js', '.css', '.html', '.json', '.yaml', '.yml')

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(target_extensions):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'rb') as f:
                        # Read the first three bytes of the file
                        head = f.read(3)
                        if head == BOM_SIGNATURE:
                            files_with_bom.append(file_path)
                except (IOError, OSError) as e:
                    print(f"Could not read {file_path}: {e}")

    return files_with_bom

if __name__ == "__main__":
    # Use the absolute path of your current project
    project_path = r"c:\Users\MD.MASTER\OneDrive\Desktop\NewRepo9\NewRepo11"
    results = find_files_with_bom(project_path)

    if results:
        print(f"Found {len(results)} file(s) with UTF-8 BOM:")
        for path in results:
            print(f" [!] {path}")
    else:
        print("No files with UTF-8 BOM detected. Your project is clean!")