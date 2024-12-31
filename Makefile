.PHONY: compile install setup

compile:
	pip install pip-tools
	pip-compile

install:
	pip install -r requirements.txt
	npm install

setup: compile install

debug_server:
	uvicorn app.main:app --reload --log-level debug

client:
	npm start
