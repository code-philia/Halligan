# Use Pixi-managed tasks inside the halligan project
.PHONY: install format lint typecheck test precommit up down models

install:
	cd halligan && pixi install

format:
	cd halligan && pixi run format

lint:
	cd halligan && pixi run lint

typecheck:
	cd halligan && pixi run typecheck

test:
	cd halligan && pixi run test

precommit:
	cd halligan && pixi run precommit

up:
	docker compose up -d --build

down:
	docker compose down -v

models:
	bash ./halligan/get_models.sh
