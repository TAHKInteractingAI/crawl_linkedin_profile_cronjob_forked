import time
from crawl_linkedin_profiles import get_driver, login_failover, scroll_linkedin
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def main():
    driver = get_driver()
    login_failover(driver)
    time.sleep(3)
    try:
        driver.get("https://www.linkedin.com/in/pauljshort")
        time.sleep(5)
        for _ in range(3):
            scroll_linkedin(driver, 1000)
            time.sleep(1)
            
        experience_xpath = (
            "//section[contains(@componentkey, 'ExperienceTopLevelSection')] | "
            "//section[.//h2[text()='Experience' or text()='Kinh nghiệm']]"
        )
        experience_section = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, experience_xpath))
        )

        entries = experience_section.find_elements(By.XPATH, ".//div[contains(@componentkey, 'entity-collection-item')]")
        
        current_companies_list = []
        job_titles_list = []

        for entry in entries:
            text_content = entry.text
            # Lọc các khối có thời gian làm việc đến hiện tại
            if not any(kw in text_content for kw in ["Present", "Hiện tại", "Hien tai"]):
                continue

            sub_roles = entry.find_elements(By.XPATH, ".//ul/li")
            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
            
            if sub_roles:
                # Trường hợp công ty có nhiều vị trí (Grouped Roles)
                company_name = lines[0]
                for role_li in sub_roles:
                    if any(kw in role_li.text for kw in ["Present", "Hiện tại", "Hien tai"]):
                        role_title = role_li.text.split('\n')[0]
                        job_titles_list.append(f"{role_title} from {company_name}")
                        if company_name not in current_companies_list:
                            current_companies_list.append(company_name)
            else:
                # Trường hợp công việc đơn lẻ (Single Role)
                if len(lines) >= 2:
                    role_title = lines[0]
                    company_name = lines[1].split(' · ')[0]
                    job_titles_list.append(f"{role_title} from {company_name}")
                    if company_name not in current_companies_list:
                        current_companies_list.append(company_name)

        company_str = ", ".join(current_companies_list)
        title_str = ", ".join(job_titles_list)
        print(f"company: {company_str}, position: {title_str}")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()