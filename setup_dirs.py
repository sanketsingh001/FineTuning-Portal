import os

# Define the project structure
directories = [
    "app/api",
    "app/api/v1",
    "app/api/v1/endpoints",
    "app/core",
    "app/db",
    "app/db/migrations",
    "app/models",
    "app/tasks",
    "ui",
    "tests"
]

# Base directory
base_dir = os.path.join("c:/", "Projectds", "Finetunig pipeline", "whisper-prep")

# Create directories
for directory in directories:
    full_path = os.path.join(base_dir, directory)
    os.makedirs(full_path, exist_ok=True)
    print(f"Created directory: {full_path}")

# Create empty __init__.py files
init_files = [
    os.path.join(base_dir, "app", "__init__.py"),
    os.path.join(base_dir, "app", "api", "__init__.py"),
    os.path.join(base_dir, "app", "api", "v1", "__init__.py"),
    os.path.join(base_dir, "app", "api", "v1", "endpoints", "__init__.py"),
    os.path.join(base_dir, "app", "core", "__init__.py"),
    os.path.join(base_dir, "app", "db", "__init__.py"),
    os.path.join(base_dir, "app", "models", "__init__.py"),
    os.path.join(base_dir, "app", "tasks", "__init__.py"),
    os.path.join(base_dir, "ui", "__init__.py"),
    os.path.join(base_dir, "tests", "__init__.py"),
]

for init_file in init_files:
    with open(init_file, 'w') as f:
        pass
    print(f"Created empty file: {init_file}")

print("\nProject structure created successfully!")
