import ast
import os
import sys


def get_imports(filepath, seen_files):
    if filepath in seen_files:
        return set()

    seen_files.add(filepath)

    imports = set()

    with open(filepath, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=filepath)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)

    return imports


def resolve_import_to_path(imp, search_paths):
    imp_parts = imp.split(".")
    for search_path in search_paths:
        candidate_path = os.path.join(search_path, *imp_parts)
        if os.path.isfile(candidate_path + ".py"):
            return candidate_path + ".py"
        elif os.path.isdir(candidate_path) and os.path.isfile(
            os.path.join(candidate_path, "__init__.py")
        ):
            return os.path.join(candidate_path, "__init__.py")
    return None


def find_all_imports(start_path):
    all_imports = set()
    seen_files = set()
    search_paths = sys.path

    def recursive_imports(filepath):
        imports = get_imports(filepath, seen_files)
        all_imports.update(imports)
        for imp in imports:
            if imp:
                imp_path = resolve_import_to_path(imp, search_paths)
                if imp_path and os.path.exists(imp_path):
                    recursive_imports(imp_path)

    recursive_imports(start_path)
    return all_imports


if __name__ == "__main__":
    start_file = "na-cli.py"
    start_path = os.path.abspath(start_file)
    all_imports = find_all_imports(start_path)
    
    all_imports.discard(None)

    print("All imports in the project:")
    for imp in sorted(all_imports):
        print(imp)
