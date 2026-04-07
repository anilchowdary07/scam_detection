#!/usr/bin/env python3
"""
Deploy scam detection environment to HuggingFace Space
"""
import os
from huggingface_hub import HfApi, create_repo
from huggingface_hub.utils import RepositoryNotFoundError

def deploy_to_huggingface():
    """Deploy the project to HuggingFace Spaces"""

    # Configuration
    repo_name = "scam-detection-env"
    username = "anilchowdary07"  # Change this to your HuggingFace username
    repo_id = f"{username}/{repo_name}"

    print("🚀 Deploying Scam Detection Environment to HuggingFace Spaces...")

    # Initialize HF API
    api = HfApi()

    try:
        # Check if repo already exists
        try:
            repo_info = api.repo_info(repo_id=repo_id, repo_type="space")
            print(f"✅ Space already exists: https://huggingface.co/spaces/{repo_id}")
        except RepositoryNotFoundError:
            # Create new space
            print(f"📝 Creating new Space: {repo_id}")
            create_repo(
                repo_id=repo_id,
                repo_type="space",
                space_sdk="docker"
            )
            print(f"✅ Space created: https://huggingface.co/spaces/{repo_id}")

        # Upload all files from current directory
        print("📤 Uploading files...")

        # List of files to upload
        files_to_upload = [
            "app.py",
            "environment.py",
            "models.py",
            "inference.py",
            "Dockerfile",
            "requirements.txt",
            "pyproject.toml",
            "openenv.yaml",
            "README.md",
            "graders/grader.py",
            "graders/__init__.py",
            "tasks/__init__.py",
            "tasks/easy.py",
            "tasks/medium.py",
            "tasks/hard.py",
            ".gitignore"
        ]

        # Upload each file
        for file_path in files_to_upload:
            if os.path.exists(file_path):
                print(f"  📄 Uploading {file_path}")
                api.upload_file(
                    path_or_fileobj=file_path,
                    path_in_repo=file_path,
                    repo_id=repo_id,
                    repo_type="space"
                )
            else:
                print(f"  ⚠️  File not found: {file_path}")

        print("🎉 Deployment complete!")
        print(f"🌐 Your Space: https://huggingface.co/spaces/{repo_id}")
        print(f"🔗 API URL: https://{username}-{repo_name}.hf.space/")
        print()
        print("⏳ Wait 2-3 minutes for the Docker build to complete.")
        print("🧪 Then test with: curl https://{}-{}.hf.space/".format(username, repo_name))

    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        print("💡 Make sure you're logged in to HuggingFace CLI:")
        print("   pip3 install huggingface_hub[cli]")
        print("   python3 -c 'from huggingface_hub import login; login()'")

if __name__ == "__main__":
    deploy_to_huggingface()