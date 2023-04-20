from flask import Flask
from selenium import webdriver

app = Flask(__name__)

@app.route("/")
def index():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.google.com")
    search_box = driver.find_element_by_name("q")
    search_box.send_keys("OpenAI")
    search_box.submit()
    search_results = driver.find_elements_by_xpath("//div[@class='g']//h3")
    result_text = ""
    for result in search_results:
        result_text += result.text + "<br>"
    driver.quit()
    return result_text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)