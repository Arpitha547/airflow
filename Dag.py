
#dag - directed acyclic graph

#tasks : 1) fetch amazon data (extract) 2) clean data (transform) 3) create and store data in table on postgres (load)
#operators : Python Operator and PostgresOperator
#hooks - allows connection to postgres
#dependencies

from datetime import datetime, timedelta
from airflow import DAG
import requests
import pandas as pd
from bs4 import BeautifulSoup
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

#1) fetch flipkart mobile data (extract) 2) clean data (transform)

headers = {
    'Accept-Language': 'en-US, en;q=0.5',
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}

s=[]


def get_flipkart_data(search_pages):
    base_url='https://www.flipkart.com/search?q=mobiles&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=off&as=off'
    page=1
    while(page<=search_pages):
        url = f"{base_url}&page={page}"
        webpage=requests.get(url,headers=headers)
        soup = BeautifulSoup(webpage.content, "html.parser")
        mobiles=soup.find_all('a',{'class':'CGtC98'})
        mobile_list=[]
        
        for mobile in mobiles:
            mobile_list.append(mobile.get('href'))
        for mobile in mobile_list:
            actual_webpage=requests.get('https://www.flipkart.com'+mobile,headers=headers)
            actual_soup=BeautifulSoup(actual_webpage.content,'html.parser')
            #print('https://www.flipkart.com'+mobile)
            product_details=actual_soup.find("span", {"class": "VU-ZEz"}).text
            Manufacturer=product_details.split()[0]
            #print(product_details.split())
            def colour(phone:list):
                if phone[0]!='Nothing':
                    for i in range(len(phone)-1):
                        if phone[i][0]=='(' :
                            if phone[i+1].isdigit()==False:
                                clr=phone[i][1:]+' '+phone[i+1][:len(phone[i+1])-1]
                            else:
                                clr=phone[i][1:len(phone[i])-1]
                        if phone[i][-1]==')':
                            break
                        
                elif phone[0]=='Nothing':
                    c=0
                    for i in range(len(phone)-1):
                        if phone[i][0]=='(' :
                            c+=1
                            if c==2 and phone[i+1].isdigit()==False:
                                clr=phone[i][1:]+' '+phone[i+1][:len(phone[i+1])-1]
                            elif c==2 and phone[i+1].isdigit()==True:
                                clr=phone[i][1:len(phone[i])-1]

                return clr
            Colour=colour(product_details.split())
            def model(phone:list):
                model=''
                for i in range(1,len(phone)):
                    if phone[i][0]!='(':
                        model+=phone[i]+' '
                    else:
                        break
                return model

            Model=model(product_details.split())
            price_details=actual_soup.find("div", {"class": "hl05eU"}).text.split()[0]

            def discounted_price(phone:str):
                price=phone[0]
                for i in  range(1,len(phone)):
                    if phone[i].isdigit()==True or phone[i]==',':
                        price+=phone[i]
                    else:break
                return price
            price=discounted_price(price_details)
            discount=actual_soup.find("div",{"class":"UkUFwK"}).text
            rating=actual_soup.find("div", {"class": "XQDdHH"}).text
          
            s.append({
                'Manufacturer':Manufacturer,
                'Model':Model,
                'Colour':Colour,
                'Price':price,
                'Discount':discount.split()[0],
                'Rating':rating
            })
        page+=1
    #df=pd.DataFrame(s)
    
    
    
    
    return s

#3) create and store data in table on postgres (load)
    
def insert_mobile_data_into_postgres(ti):
    mobile_data = ti.xcom_pull(task_ids='fetch_mobile_data')
    

    postgres_hook = PostgresHook(postgres_conn_id='mobiles_connection')
    insert_query = """
    Truncate table mobiles;
    INSERT INTO mobiles (Manufacturer, Model, Colour, Price, Discount, Rating)
    VALUES (%s, %s, %s, %s, %s,%s)
    """
    for mobile in mobile_data:
        postgres_hook.run(insert_query, parameters=(mobile['Manufacturer'], mobile['Model'], mobile['Colour'], mobile['Price'], mobile['Discount'], mobile['Rating']))


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 28),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'fetch_and_store_flipkart_mobiles_f3',
    default_args=default_args,
    description='A simple DAG to fetch mobile data from Flipkart and store it in Postgres',
    schedule_interval=timedelta(days=1),
)

#operators : Python Operator and PostgresOperator
#hooks - allows connection to postgres


fetch_mobile_data_task = PythonOperator(
    task_id='fetch_mobile_data',
    python_callable=get_flipkart_data,
    op_args=[5],  # Number of pages to fetch
    dag=dag,
)

create_table_task = PostgresOperator(
    task_id='create_table',
    postgres_conn_id='mobiles_connection',
    sql="""
    CREATE TABLE IF NOT EXISTS mobiles (
        id SERIAL PRIMARY KEY,
        Manufacturer TEXT NOT NULL,
        Model TEXT,
        Colour TEXT,
        Price Text,
        Discount TEXT,
        Rating TEXT
    );
    """,
    dag=dag,
)

insert_mobile_data_task = PythonOperator(
    task_id='insert_mobile_data',
    python_callable=insert_mobile_data_into_postgres,
    dag=dag,
)

#dependencies

fetch_mobile_data_task >> create_table_task >> insert_mobile_data_task
