import os, io, time
from datetime import datetime, timezone
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title='Morning Breakout Scanner', layout='wide', page_icon='📈')
st.title('📈 Morning Breakout Scanner')
st.caption('Research dashboard • Not a broker or trading signal • Verify data freshness and corporate actions')

COUNTRIES=['United States','China','Singapore','Hong Kong','Canada','Israel','United Kingdom','Other']
SCHEMA=['ticker','company','price','prev_close','float_m','rvol','premarket_high','opening_high_5m','exchange','incorporation_country','news_title','news_url','catalyst_status','ipo_date','asof']

@st.cache_data(ttl=60,show_spinner=False)
def snapshots(key):
    r=requests.get('https://api.massive.com/v2/snapshot/locale/us/markets/stocks/tickers',params={'apiKey':key},timeout=35)
    r.raise_for_status()
    obj=r.json()
    if obj.get('status') not in ('OK','DELAYED') and not obj.get('tickers'):
        raise ValueError(str(obj)[:300])
    rows=[]
    for x in obj.get('tickers',[]):
        day=x.get('day') or {}; prev=x.get('prevDay') or {}; trade=x.get('lastTrade') or {}
        price=trade.get('p') or day.get('c') or day.get('o')
        close=prev.get('c')
        if not price or not close: continue
        rows.append({'ticker':x.get('ticker'),'price':price,'prev_close':close,'gain_pct':100*(price/close-1),'volume':day.get('v'),'asof':datetime.now(timezone.utc).isoformat()})
    return pd.DataFrame(rows)

def demo():
    return pd.DataFrame([
        dict(ticker='DEMO1',company='Example Robotics',price=4.65,prev_close=3.75,float_m=6.1,rvol=4.8,premarket_high=4.55,opening_high_5m=4.60,exchange='NASDAQ',incorporation_country='United States',news_title='Example product announcement',news_url='',catalyst_status='Yes',ipo_date='',asof='DEMO ONLY'),
        dict(ticker='DEMO2',company='Example Biotech',price=12.40,prev_close=10.50,float_m=3.4,rvol=6.2,premarket_high=12.10,opening_high_5m=12.30,exchange='NASDAQ',incorporation_country='Singapore',news_title='Example trial update',news_url='',catalyst_status='Yes',ipo_date='',asof='DEMO ONLY'),
        dict(ticker='DEMO3',company='Example Software',price=8.10,prev_close=7.80,float_m=8.0,rvol=1.3,premarket_high=8.30,opening_high_5m=8.40,exchange='NYSE',incorporation_country='Canada',news_title='',news_url='',catalyst_status='Unknown',ipo_date='',asof='DEMO ONLY')])

with st.sidebar:
    st.header('Connection')
    mode=st.radio('Data source',['Demo','Massive API','Upload CSV'])
    key=st.text_input('Massive API key',type='password',value=os.getenv('MASSIVE_API_KEY','')) if mode=='Massive API' else ''
    upload=st.file_uploader('Upload scanner CSV',type='csv') if mode=='Upload CSV' else None
    st.header('Filters')
    lo,hi=st.slider('Price ($)',0.0,100.0,(1.0,20.0),0.5)
    maxfloat=st.number_input('Maximum float (millions)',value=10.0,min_value=0.1)
    mingain=st.number_input('Minimum gain (%)',value=10.0)
    minrvol=st.number_input('Minimum RVOL',value=3.0,min_value=0.0)
    selected=st.multiselect('Country of incorporation',COUNTRIES,default=COUNTRIES)
    news_only=st.checkbox('Require confirmed news/catalyst',value=False)
    ipo_only=st.checkbox('Only IPO-tagged stocks',value=False)
    breakout_only=st.checkbox('Above 5-minute opening high',value=False)
    strict=st.checkbox('Exclude stocks with unknown float/RVOL/country',value=True)
    refresh=st.button('🔄 Refresh data')
    st.caption('Mobile tip: tap the sidebar arrow to hide filters. Refresh is manual; no push alerts or automatic orders.')
if refresh: snapshots.clear()

try:
    if mode=='Demo': df=demo(); st.warning('DEMO MODE — All symbols and prices are fictional.')
    elif mode=='Upload CSV':
        if upload is None: st.info('Upload a CSV using the supplied schema to begin.'); st.stop()
        df=pd.read_csv(upload)
    else:
        if not key: st.info('Enter your Massive API key in the sidebar.'); st.stop()
        df=snapshots(key)
        if df.empty: st.warning('The API returned no priced stocks.'); st.stop()
        st.info('Massive snapshot loaded. Float, RVOL, company incorporation, IPO and news require separate enrichment. Upload an enrichment CSV below; unknown values are never guessed.')
        enrich=st.file_uploader('Optional enrichment CSV (ticker plus any schema columns)',type='csv',key='enrich')
        if enrich:
            extra=pd.read_csv(enrich).drop_duplicates('ticker')
            df=df.merge(extra,on='ticker',how='left',suffixes=('','_enrich'))
            for c in list(df.columns):
                if c.endswith('_enrich'):
                    base=c[:-7]
                    df[base]=df[base].combine_first(df[c]) if base in df else df[c]
                    df=df.drop(columns=[c])
except Exception as e:
    st.error(f'Data connection failed: {e}. Check your API key, plan access, and network.'); st.stop()

for c in SCHEMA:
    if c not in df: df[c]=pd.NA
for c in ['price','prev_close','float_m','rvol','premarket_high','opening_high_5m']:
    df[c]=pd.to_numeric(df[c],errors='coerce')
df['gain_pct']=(df['price']/df['prev_close']-1)*100
country=df['incorporation_country'].fillna('').astype(str).str.strip()
known=country.isin(COUNTRIES[:-1]); grouped=country.where(known,'Other')
mask=df['price'].between(lo,hi)&df['gain_pct'].ge(mingain)
if strict:
    mask &= df['float_m'].le(maxfloat)&df['rvol'].ge(minrvol)&country.ne('')
else:
    mask &= (df['float_m'].le(maxfloat)|df['float_m'].isna())&(df['rvol'].ge(minrvol)|df['rvol'].isna())
mask &= grouped.isin(selected)
if news_only: mask &= df['catalyst_status'].fillna('').astype(str).str.lower().isin(['yes','true','confirmed'])
if ipo_only: mask &= df['ipo_date'].notna() & df['ipo_date'].astype(str).str.strip().ne('')
if breakout_only: mask &= df['opening_high_5m'].notna() & df['price'].gt(df['opening_high_5m'])
result=df[mask].sort_values('gain_pct',ascending=False)
a,b,c=st.columns(3)
a.metric('Matching stocks',len(result)); b.metric('Stocks evaluated',len(df)); c.metric('Feed','DEMO' if mode=='Demo' else 'API' if mode=='Massive API' else 'CSV')
st.subheader('Top gainers matching your filters')
columns=['ticker','company','price','gain_pct','float_m','rvol','volume','incorporation_country','exchange','news_title','news_url','ipo_date','asof']
columns=[c for c in columns if c in result]
st.dataframe(result[columns],hide_index=True,use_container_width=True,column_config={'gain_pct':st.column_config.NumberColumn('Gain %',format='%.2f%%'),'price':st.column_config.NumberColumn('Price',format='$%.2f'),'news_url':st.column_config.LinkColumn('News link')})
st.download_button('Download matching stocks as CSV',result.to_csv(index=False).encode(),file_name='scanner_matches.csv',mime='text/csv')
st.divider()
st.subheader('Breakout watch (informational)')
st.caption('Breakout is a simple price-above-supplied-5-minute-high condition, not a live streaming alert. Opening highs must be populated from minute-bar data.')
watch=df[df['opening_high_5m'].notna()&df['price'].gt(df['opening_high_5m'])]
st.write(f'{len(watch)} stocks above a supplied 5-minute opening high.')
st.caption('RVOL must be supplied from comparable historical intraday volume; daily volume divided by yesterday’s volume is NOT RVOL. Float means freely tradable shares, not shares outstanding. Exchange identifies listing venue, not incorporation country. Data latency depends on provider plan.')
