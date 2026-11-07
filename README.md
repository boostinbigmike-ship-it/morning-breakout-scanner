# Morning Breakout Scanner

## Run locally

1. Install Python 3.10 or newer from python.org.
2. Unzip this folder. Open a terminal inside it.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python -m streamlit run app.py`.
5. Open the local URL displayed, usually `http://localhost:8501`.

Start in Demo mode. For actual U.S.-listed market snapshots, obtain an API key at https://massive.com and choose **Massive API** in the sidebar. Snapshot access requires a supported paid plan; data may be delayed depending on your subscription. API credentials are typed into the app, not embedded in the source. Do not share keys or commit them to GitHub.

## Important limitations

- The Massive snapshot returns prices and volume, **not** complete float, RVOL, IPO, incorporation country, or news enrichment. The dashboard does **not** invent these. Upload a separate enrichment CSV with `ticker` and relevant columns; blank unknowns remain blank.
- By default, strict filters exclude stocks missing float, RVOL or country, so the raw snapshot may produce **zero matches**. Uncheck the strict filter only to explore unverified candidates.
- To compute real intraday RVOL, collect time-of-day cumulative volume across comparable previous sessions and compare with today's cumulative volume at the same time. Do not confuse with volume divided by yesterday's full-day volume.
- News and IPO filters work only with supplied verified fields. They are not automatically fetched in this version.
- The breakout watch checks supplied opening 5-minute highs; it is not a streaming or push alert service.
- The provider covers U.S.-listed stocks, including foreign-incorporated issuers, not all shares traded on foreign exchanges. Exchange and incorporation country are separate.
- No Webull brokerage connection or order placement is implemented.
- For internet deployment, Streamlit Community Cloud can run this app from a GitHub repository. Use its Secrets feature for any server-side credentials and assess provider licensing before sharing data.


## Publish from an Android phone (GitHub + Streamlit Community Cloud)

1. Download the ZIP and extract it in Android's Files/My Files app.
2. In Chrome, sign up at https://github.com/signup and verify your email.
3. At https://github.com/new create a **private** repository named `morning-breakout-scanner`.
4. In the new repository choose **Add file → Upload files**. Select `app.py`, `requirements.txt`, `README.md`, and optionally `sample_schema.csv` **from inside** the extracted `morning_breakout_scanner` folder (not the ZIP itself). Commit changes. On mobile, Chrome's **Desktop site** option may help.
5. Go to https://share.streamlit.io, sign in with GitHub, choose **Create app**, pick the repository and branch, and set **Main file path** to `app.py`. Deploy. If your private repository isn't visible, check the GitHub permissions granted to Streamlit.
6. Open the resulting `*.streamlit.app` URL in Chrome. Choose **Demo** in the sidebar to test. In Chrome's three-dot menu choose **Add to Home screen** for a shortcut.
7. For market data, get a compatible Massive API subscription and API key at https://massive.com. In the sidebar switch to **Massive API**, paste your key into the password field, and tap **Refresh data**. Do not put the key in GitHub, screenshots, or shared messages.

**Security note:** For shared deployments, entering a key in a Streamlit password field may expose that key to server-side app sessions; use your own trusted app deployment. To configure the key as a server environment variable in your own host, set `MASSIVE_API_KEY`. For Community Cloud you may instead modify the code to read `st.secrets` and set the key in Streamlit's app secrets, not in the repository.

**Why are there zero matches in live mode?** The default strict filter requires float, RVOL and incorporation country, which the snapshot endpoint alone doesn't supply. Use an enrichment CSV or temporarily uncheck **Exclude stocks with unknown float/RVOL/country** to explore candidates (not validated matches).

**Market-data timing:** API plan permissions, delay, and coverage vary. A refresh is not a push alert. This is a research prototype, not a production-grade real-time trading system.
