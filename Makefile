.PHONY: test fia-data-ne fia-clean-ne

test:
	python -m unittest discover -s tests -v

fia-data-ne:
	python -m tree_age.fia.cli download

fia-clean-ne:
	python -m tree_age.fia.cli clean

