import asyncio
import json
import os

class IngredientStorage:
    CRITICAL_THRESHOLD = 5

    def __init__(self, filename: str):
        self.filename = filename
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def check_and_subtract(
        self,
        ingredients_needed: dict[str, int]
    ) -> tuple[bool, str, list[str]]:
        async with self._get_lock():
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            missing = []
            for ing, qty in ingredients_needed.items():
                available = data.get(ing, 0)
                if available < qty:
                    missing.append(f"{ing} (disponível: {available}, necessário: {qty})")

            if missing:
                return False, f"Ingredientes insuficientes: {', '.join(missing)}", []

            for ing, qty in ingredients_needed.items():
                data[ing] = data.get(ing, 0) - qty

            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            critical_alerts = []
            for ing in ingredients_needed:
                rem = data.get(ing, 0)
                if rem <= self.CRITICAL_THRESHOLD:
                    critical_alerts.append(f"{ing} ({rem} restantes)")

            return True, "sucesso", critical_alerts

    def subtract(self, ingredients_difference: dict[str, int]):
        with open(self.filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for ingredient_name, quantity_used in ingredients_difference.items():
            if ingredient_name not in data:
                continue
            data[ingredient_name] = data[ingredient_name] - quantity_used

        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    storage_path = os.path.join(os.path.dirname(__file__), 'data.json')
    s = IngredientStorage(storage_path)
    s.subtract({ 'lettuce': 2, 'onion': 3 })

