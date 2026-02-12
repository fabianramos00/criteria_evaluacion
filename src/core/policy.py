from src.config.settings import settings
from src.core.tools import get_schema_resume, is_similar
from src.api.schemas import PolicySchema
import asyncio
from playwright.async_api import async_playwright


async def get_boai(repository_name: str) -> str | None:
    rows = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page()

        await page.goto(
            settings.BOAI_URL,
            wait_until="networkidle"
        )

        await page.fill('input[name="combo_search"]', f'"{repository_name}"')
        await page.click('input[type="submit"]')
        await page.click('input[type="submit"]')
        await asyncio.sleep(2)
        rows = await page.locator("li.list-group-item span.organization-field").all_text_contents()
        await browser.close()
    for repository_name_boai in rows:
        if is_similar(repository_name_boai, repository_name):
            return repository_name_boai
    return None


async def get_boai_score(repository_name_list: list[str]) -> tuple[int, str | None]:
    for repository_name in repository_name_list:
        boai_repository = await get_boai(repository_name)
        if boai_repository:
            return 1, boai_repository
    return 0, None


async def evaluate_policy(repository_name_list: list[str], policy_schema: PolicySchema):
    policy_resume =  get_schema_resume(policy_schema.dict())
    boai_score, boai_repository = await get_boai_score(repository_name_list)
    policy_resume['boai'] = {
        'value': boai_score,
        'name': boai_repository
    }
    policy_resume['total'] = sum(
        v['value'] if isinstance(v, dict) else v for v in policy_resume.values()
    )
    return policy_resume
