import os

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        if ".git" in root:
            continue
        
        level = root.replace(startpath, "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}📄 {f}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"--- リポジトリ内のファイル一覧 ({current_dir}) ---")
    list_files(current_dir)
