"""Approved source registry. No request may supply an arbitrary download URL."""
SOURCES = {
 'world-bank': {'id':'world-bank','title':'World Bank · World Development Indicators','url':'https://data.worldbank.org','docs':'https://datahelpdesk.worldbank.org/knowledgebase/articles/889392','method':'Scheduled API','cadence':'Daily checks; publisher release dates vary','max_age_days':7},
 'undp': {'id':'undp','title':'UNDP · Human Development Reports','url':'https://hdr.undp.org/data-center/documentation-and-downloads','method':'Reviewed dataset import','cadence':'Edition-based','max_age_days':45},
 'niti': {'id':'niti','title':'NITI Aayog · State Health Index','url':'https://www.niti.gov.in/node/366','method':'Reviewed report import','cadence':'Edition-based','max_age_days':90},
 'henley': {'id':'henley','title':'Henley & Partners','url':'https://www.henleyglobal.com/passport-index/methodology','method':'Publisher release; access required','cadence':'Check publisher release','max_age_days':45},
 'survey': {'id':'survey','title':'Ministry of Finance · Economic Survey','url':'https://www.indiabudget.gov.in/economicsurvey/','method':'Official chapters; reviewed figures','cadence':'Annual edition','max_age_days':45},
}
def wb(id,title,code,unit,category,definition,direction='neutral'):
 return dict(id=id,title=title,code=code,unit=unit,category=category,definition=definition,direction=direction,source_id='world-bank',kind='indicator',scope='world',methodology='World Development Indicators · '+code)
METRICS = {
 m['id']:m for m in [
 wb('gdp','GDP','NY.GDP.MKTP.CD','current US$','Economy','Gross domestic product at current US dollar prices. Exchange rates affect this measure.'),
 wb('gdp-growth','Real GDP growth','NY.GDP.MKTP.KD.ZG','%','Economy','Annual percentage growth of GDP at constant prices.'),
 wb('gdp-per-capita','GDP per capita','NY.GDP.PCAP.CD','current US$ per person','Economy','GDP divided by midyear population; this is not household income.'),
 wb('population','Population','SP.POP.TOTL','people','Population','Total population, using the World Bank country/economy coverage.'),
 wb('inflation','Consumer price inflation','FP.CPI.TOTL.ZG','%','Economy','Annual percentage change in the consumer price index.'),
 wb('life-expectancy','Life expectancy','SP.DYN.LE00.IN','years','Health','Life expectancy at birth, total population. A health measure, not an overall health index.','higher'),
 wb('infant-mortality','Infant mortality','SP.DYN.IMRT.IN','per 1,000 live births','Health','Deaths before age one per 1,000 live births.','lower'),
 dict(id='hdi',title='Human Development Index',unit='index (0–1)',category='Development',definition='Composite index of health, education and standard of living. Published country ranks are retained.',direction='higher',source_id='undp',kind='index',scope='world',methodology='UNDP HDR 2025 technical methodology'),
 dict(id='passport',title='Henley Passport Index',unit='destinations',category='Mobility',definition='Passport access without a prior visa under the publisher’s rules. Rank and access score depend on the release.',direction='higher',source_id='henley',kind='index',scope='world',methodology='Henley Passport Index'),
 dict(id='state-health',title='State Health Index',unit='index score',category='Health',definition='Overall health performance within the publisher’s separate larger-state, smaller-state and Union Territory groups.',direction='higher',source_id='niti',kind='index',scope='states',methodology='NITI State Health Index · Round IV'),
 ]
}
HDI_URL='https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Composite_indices_complete_time_series.csv'
NITI_URL='https://www.niti.gov.in/sites/default/files/2023-02/NITI-WB_Health_Index_Report_24-12-21.pdf'
SURVEY_URL=SOURCES['survey']['url']
SURVEYS = [{
 'id':'2025-26','title':'Economic Survey 2025–26','source_url':SURVEY_URL,
 'description':'Explore the official chapters and statistical appendix. Figures remain attached to this edition; newer releases do not overwrite it.',
 'appendix_url':SURVEY_URL+'doc/Statistical-Appendix-in-English.pdf',
 'chapters':[
  {'id':str(i),'title':title,'source_url':SURVEY_URL+f'doc/eschapter/echap{i:02}.pdf'} for i,title in enumerate([
   'State of the economy','Fiscal developments','Monetary management and financial intermediation','External sector','Inflation','Agriculture and food management','Services','Industry','Investment and infrastructure','Environment and climate change','Education and health','Employment and skill development','Rural development and social progress','Evolution of the AI ecosystem in India','Urbanisation','From import substitution to strategic resilience',
  ],1)
 ]
}]

# Exact chapter links checked against the official edition catalogue.
SURVEYS[0]['chapters'][-1]['source_url']=SURVEY_URL+'doc/eschapter/echap16-1.pdf'
SURVEYS[0]['chapters'][-1]['id']='16-1'
SURVEYS[0]['chapters'].append({'id':'16-2','title':'Strategic resilience: the state, private sector and citizens','source_url':SURVEY_URL+'doc/eschapter/echap16-2.pdf'})
SURVEYS[0]['chapters'][0].update({
 'brief':'The opening chapter examines demand, investment and sectoral growth. The figures below are the Survey’s first advance estimates for FY2025–26; later statistical releases may revise them.',
 'figures':[
  {'title':'Real GDP growth','value':'7.4%','period':'FY2025–26','status':'First advance estimate','citation':'Chapter 1 · Table I.2a · printed page 9'},
  {'title':'Real GVA growth','value':'7.3%','period':'FY2025–26','status':'First advance estimate','citation':'Chapter 1 · Table I.2a · printed page 9'},
 ],
})

SOURCES['niti']['watch_url']='https://www.niti.gov.in/divisions/division/health-and-family-welfare'

# Catalogue metadata captured from the official 2025–26 edition on 15 Nov 2026.
import json as _json
from pathlib import Path as _Path
SURVEYS[0]['tables']=_json.loads((_Path(__file__).parents[1]/'data/stats/survey-2025-26-tables.json').read_text())
