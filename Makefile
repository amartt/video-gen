# Run main file to generate audio files
run:
	python generate_audio.py

# Clean up log and output file directories
clean:
	rm -rf logs/ generated_files/

# Update .dockerignore, requirements.txt, and .env-template
# Add, commit, and push to a specified branch and remote
update:
	python setup_files.py
	git add .
	git commit -m "$(msg)"
	git push origin main