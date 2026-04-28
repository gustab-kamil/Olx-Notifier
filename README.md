# :bell: Olx Notifier
Follow ads for your chosen category on OLX.pl
## :book: Description
It is a Python scraper for checking and saving active OLX ads from one or more search URLs.
## 🚀 Usage
Make sure you have installed:
* [alive_progress](https://pypi.org/project/alive_progress)
* [BeautifulSoup4](https://pypi.org/project/beautifulsoup4)
* [certifi](https://pypi.org/project/certifi)
* [lxml](https://pypi.org/project/lxml/)
* [telegram_send](https://pypi.org/project/telegram_send/)

Install dependencies with:

```bash
pip install -r requirements.txt
```

### Notifying

You can choose between these notification options:
- By telegram message (preferred option)
- By ntfy.sh
- Or disable notifications with `no-notify`
---
### a) Notifying by telegram message
To do so you first need to configure your `telegram_send` package.

To do so:
1. First create your new telegram bot by writing on telegram to the `BotFather` on telegram, and create new bot by using command `/newbot`.
2. After filling all needed data you will be given you HTTP API token for your bot.
3. In CLI use command `telegram-send configure` - paste your token there, then add your freshly created bot on telegram and send him your activation password (code).
4. Voi'la - you can simply use your bot!

---
### b) Notifying by [ntfy.sh](https://ntfy.sh) (preffered option)
To do so you first need to configure your receiver decice - with [ntfy](https://ntfy.sh) app.

Then you create your topic, subscribe to it on the receiver and provide the topic in the `--notify` option like this: (--notify ntfy_<your_topic>)

---
### URLs

You can scrape one URL or multiple URLs in a single run.

If you pass multiple URLs, the script will:
1. Scrape them one by one.
2. Wait 30 seconds between URLs.
3. Merge and deduplicate ads before comparing them with `previous_results.txt`.

If you do not pass `--url`, the script uses the `given_urls` list inside [main.py](./main.py).

---
### Run

To start - just run the following command at the root of your project like e.g.:
```bash
python3 main.py --notify telegram --url <your-url>
python3 main.py --notify ntfy_<your_topic> --url <your-url>
python3 main.py --notify no-notify --url <your-url>
python3 main.py --debug --notify ntfy_<your_topic> --url <url-one> <url-two>
python3 main.py --debug --notify telegram
```

Example with multiple URLs:

```bash
python3 main.py --debug --notify ntfy_kamil-flat2026 \
	--url "https://www.olx.pl/search-url-1" \
				"https://www.olx.pl/search-url-2"
```

Notes:
- `--notify telegram` uses your `telegram_send` configuration.
- `--notify ntfy_<topic>` sends messages to the given ntfy topic.
- `--notify no-notify` only updates `previous_results.txt` and logs.
- `--debug` prints logs to the terminal and also writes them to `logs.log`.

Or schedule it to run every X minutes on your machine, by using e.g. crontab like:
```bash
| every 10min   | your path to scrapper catalog | path to your python    | parameters
*/10 * * * * cd /home/{your-user}/Olx-Notifier; /usr/bin/python3 main.py --notify telegram
```

## Author

👤 **Kamil Gustab**

- Github: [@gustab.kamil](https://github.com/kamil-gustab)
