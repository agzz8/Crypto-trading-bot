"""backtesting.py will:
    Open a selenium browser
    Test a Tradingview strategy for each stock or cryptocurrency in a predefined watchlist
    Generate extra metrics
    Save strategy metrics in a CSV file for further revision

Instructions:
    Open your TradingView account
    Apply the strategy to be tested to the active chart
    If multiple charts are open, close all and leave the main chart open
    Open the watchlist to be tested
    Select the time interval
    Save the session and close TradingView
    Run backtesting.py
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd
import re
#from PIL import Image

# CONFIG START
tradingview_username = "USERNAME"
tradingview_password = "PASSWORD"
strategy_name = "E6c.v8"
strategy_results_file = "reports/"+strategy_name+"-tradingview-report.csv"
# Select the last ticker in the watchlist to be tested
last_ticker = "XLMUSDT"
# CONFIG END


def wait_and_click(browser, path):
    WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, path))).click()


def concat_ticker(row):
    return "BINANCE:"+str(row['symbol'])


def open_and_login(driver, username, password):
    driver.get("https://www.tradingview.com/#signin")
    driver.find_element_by_class_name("js-show-email").click()
    driver.find_element_by_name("username").send_keys(username)
    driver.find_element_by_name("password").send_keys(password)
    driver.find_element_by_xpath("//button[@type='submit']").click()
    driver.maximize_window()
    time.sleep(5)
    driver.find_element_by_link_text('Chart').click()
    time.sleep(10)


def get_tickers(driver):
    tickers = driver.find_elements_by_class_name("symbol-EJ_LFrif")
    return tickers


def main():
    # The last empty columns are for manual revision and to edit directly in Excel
    df = pd.DataFrame(columns=['e', 'symbol', 'Net Profit', 'Total Closed Trades', 'Percent profitable', 'Profit factor', 'Max Drawdown',
                      'Avg Trade', 'Avg num of bars', 'USDT-hour', 'USDT-hour-profitability', 'Pre-filter', 'Active', 'Loss at the end', 'Notes', 'margin10'])

    chrome_options = Options()
    # Stops the UI interface (chrome browser) from popping up
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(
        executable_path='/usr/bin/chromedriver', options=chrome_options)
    wait = WebDriverWait(driver, 10)

    open_and_login(driver, tradingview_username, tradingview_password)

    tickers = get_tickers(driver)
    ticker = tickers[0]
    val = ticker.get_attribute("data-symbol-short")
    i = 1
    # Loop though all symbols in watchlist until the last ticker:
    while True:
        # TODO end script after last ticker automatically
        if val == last_ticker:
            break
        if i == 0:
            ticker.click()
            time.sleep(5)
        else:
            # Next ticker
            actions = ActionChains(driver)
            actions.send_keys(Keys.DOWN).perform()
            time.sleep(5)
            elementx = wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'active-EJ_LFrif')))
            ticker = driver.find_element_by_class_name("active-EJ_LFrif")
            val = ticker.get_attribute("data-symbol-short")
        # Extract performance summary of the strategy
        report = driver.execute_script("var myList=[];arguments[0].forEach(function(element) {myList.push(element.textContent);});return myList;", driver.find_elements_by_css_selector(
            ".report-data > .data-item > strong"))
        # Check if strategy is not profitable or has no trade signals
        if len(report) < 7:
            df.loc[i] = [strategy_name] + [val] + \
                [0, 0, 0, 0, 0, 0, 0, 0, 0, "", "", "", "", ""]
        else:
            for ii in range(len(report)):
                report[ii] = re.sub('[^0-9.]', '', report[ii])
            # Append extra profitability metrics
            report.append(float(report[5]) / float(report[6]))
            report.append(report[7] * float(report[2])/100)
            df.loc[i] = [strategy_name] + [val] + report + ["", "", "", "", ""]
        i = i+1
        print(df.tail())
        df.to_csv(strategy_results_file, index=False)
    df['ticker'] = df.apply(concat_ticker, axis=1)
    final_df = df.sort_values(by=['USDT-hour-profitability'], ascending=False)
    final_df.to_csv(strategy_results_file, index=False)
    time.sleep(5)
    driver.quit()


if __name__ == "__main__":
    main()
