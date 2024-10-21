# Run main python file to generate audio files
run:
	python3 generate_audio.py

# Clean up log and output file directories
clean:
	rm -rf logs/ generated_files/

# Add, commit, and push to a specified branch and remote
update:
	git add .
	git commit -m "$(msg)"
	git push origin main