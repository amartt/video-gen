# Run main file to generate audio files
run:
	python generate_audio.py

# Clean up log and output file directories
clean:
	rm -rf logs/ generated_files/ __pycache__/

# Clean up unneeded packages and dependencies in environment
# Update .dockerignore, requirements.txt, and .env-template
env:
	python cleanup_env.py
	python setup.py

# Add, commit, and push to a specified branch and remote
update:
	git add .
	git commit -m "$(msg)"
	git push origin main