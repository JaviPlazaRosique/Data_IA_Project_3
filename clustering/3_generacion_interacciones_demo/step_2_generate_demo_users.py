from __future__ import annotations

import argparse
import csv
import random
import uuid
from pathlib import Path

from demo_config import (
    DEFAULT_SEED,
    DEMO_USERS_PATH,
    PERSONAS,
    ensure_output_dir,
    weighted_choice,
)


FIELDNAMES = [
    "user_id",
    "persona",
    "home_city",
    "planned_swipes",
    "target_price",
    "city_loyalty",
    "chat_share",
    "exploration_factor",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic demo users.")
    parser.add_argument("--output-csv", type=Path, default=DEMO_USERS_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def build_user_id(persona_name: str, index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"clustering-demo:{persona_name}:{index:04d}"))


def main() -> None:
    args = parse_args()
    ensure_output_dir()
    rng = random.Random(args.seed)

    users: list[dict[str, str | int | float]] = []
    for persona in PERSONAS:
        for index in range(1, persona.user_count + 1):
            user_id = build_user_id(persona.name, index)
            home_city = weighted_choice(
                list(persona.preferred_cities),
                [1.0 / len(persona.preferred_cities)] * len(persona.preferred_cities),
                rng,
            )
            planned_swipes = rng.randint(*persona.swipe_range)
            users.append(
                {
                    "user_id": user_id,
                    "persona": persona.name,
                    "home_city": home_city,
                    "planned_swipes": planned_swipes,
                    "target_price": persona.target_price,
                    "city_loyalty": persona.city_loyalty,
                    "chat_share": persona.chat_share,
                    "exploration_factor": persona.exploration_factor,
                }
            )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(users)

    print(f"Generated {len(users)} demo users in {args.output_csv}")


if __name__ == "__main__":
    main()
