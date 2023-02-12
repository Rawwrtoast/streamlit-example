from collections import namedtuple
import altair as alt
import math
import pandas as pd
import streamlit as st

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly
st.set_option('deprecation.showfileUploaderEncoding', False) #to run streamlit forever and dynamically refresh when source code is updated.
from google.oauth2 import service_account
from google.cloud import storage

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = storage.Client(credentials=credentials)

# Retrieve file contents.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def read_file(bucket_name, file_path):
    bucket = client.bucket(bucket_name)
    content = bucket.blob(file_path).download_as_string().decode("utf-8")
    return content

bucket_name = "snake_apartment"
file_path = "cleandata.csv"

content = read_file(bucket_name, file_path)
#---------------------------------------------------------------------------------------------------
# Print results.
for line in content.strip().split("\n"):
    name, pet = line.split(",")
    st.write(f"{name} has a :{pet}:")
#Data Types for each column
dtypes = {'RegionCode': int,
          'City': str ,'District': str, 'Neighbourhood': str,'remainingAddr': str, 
          'latitude': float,'longitude': float,'Apartment': str,'postalcode': str,
          'placeId': str,'Lot':str, #TradingDay: datetime
          'FloorArea': float,'Floor': int,'YrBuilt': int,'TransAmt': float,'KRAddr': str}

#Import data
df = pd.read_csv('cleandata.csv',sep=',', dtype = dtypes, parse_dates=['TradingDay'], on_bad_lines = 'warn')
df['latitude'] = df['latitude'].astype(float)
df['longitude'] = df['longitude'].astype(float)
originalrow_count = len(df.index)
df = df.dropna(subset=['City', 'latitude', 'longitude', 'TransAmt','TradingDay']) #Drop record if cols City, latitude, longitude, TransAmt, or TradingDay is None (any) 
print(f"Dropped {originalrow_count-len(df.index)} records.")
df.info()

print(df.head(5)) #example data

#STREAMLIT
st.write("Dashboard to view South Korea apartment sales history")
#st.write(df) #make this chunky, too large
#------------------------------------------GRAPHS START HERE----------------------------------------------------
#1. naming format: type_what it shows_variable ordered by 
data_column = st.selectbox("Select data column", df.columns)
group_column = st.selectbox("Select grouping column", df.columns)
df_grouped = df.groupby(group_column)[data_column].sum().reset_index()
fig = px.bar(df_grouped, x=group_column, y=data_column)
st.plotly_chart(fig)


#LINE GRAPH, see price trend over time, compare median and mean
df['TradingDay'] = pd.to_datetime(df['TradingDay'], format='%Y/%m/%d')
# group by the TradingDay column and calculate the mean and median of the Price column
df_grouped_month = df.groupby(pd.Grouper(key='TradingDay', freq='M'))['TransAmt'].agg(['median', 'mean']).reset_index()
# convert the TradingDay column to the desired format
df_grouped_month['TradingDay'] = df_grouped_month['TradingDay'].dt.strftime('%B/%y')
line_avgmedprice_by_month = px.line(df_grouped_month, x='TradingDay', y=['median', 'mean'])
line_avgmedprice_by_month.update_traces(mode='markers+lines')
st.plotly_chart(line_avgmedprice_by_month)


st.write("Price range of Apartments")
ordersOfMag_list = ["", "Thousand", "Million", "Billion", "Trillion"]
for i in range(3,-1,-1):
    orderOfMag = 1000**i
    if (min := df['TransAmt'].min() / orderOfMag) > 0:
        min = str(min) + " " + ordersOfMag_list[i]
        break
for i in range(4,-1,-1):
    orderOfMag = 1000**i
    if (max := df['TransAmt'].max() / orderOfMag) > 0:
        max = str(max) + " " + ordersOfMag_list[i]
        break
min + " - " + max

#Show distribution of apartment sales
#Create histogram
hist_apartmentsales_by_price = plotly.graph_objs.Figure(data=[plotly.graph_objs.Histogram(x=df['TransAmt'], nbinsx=5000)])
hist_apartmentsales_by_price.update_layout(
    title='Distribution of Apartment Sales',
    xaxis_title='Value',
    yaxis_title='Frequency',
    bargap=0.1
)
st.plotly_chart(hist_apartmentsales_by_price)

#Calculate the cost per floor area (m^2)
df['cost_per_area'] = df['TransAmt'] / df['FloorArea']
#Plot the graph
fig_cost_per_area_by_district = px.violin(df, x='District', y='cost_per_area', title="Cost per Area m^2 in different districts") 
st.plotly_chart(fig_cost_per_area_by_district)


#order by district, cost per area, avg cost
# group by the TradingDay column and calculate the mean and median of the Price column
df_grouped_district = df.groupby(pd.Grouper(key =['City', "District"]))['TransAmt'].agg(['median', 'mean', "sum"]).reset_index()
df_grouped_district = df.groupby(pd.Grouper(key =['City', "District"]))['cost_per_area'].agg(['median', 'mean', "sum"]).reset_index()


bar_avgmedprice_district = px.bar(df_grouped_district, x='District', y=['TransAmt', 'cost_per_area']['median', 'mean'])
bar_sumprice_district = px.bar(df_grouped_district, x='District', y=['TransAmt', 'cost_per_area']['sum'])
st.plotly_chart()
# show chart

# # Plot the first bar chart
# df_filtered_11000_12000 = df_filtered[df_filtered['District'].between(11000,12000)]
# fig2_11000_12000 = px.bar(df_filtered_11000_12000, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (11000-12000)')

# # Plot the second bar chart
# df_filtered_26000_32000 = df_filtered[df_filtered['District'].between(26000, 32000)]
# fig2_26000_32000 = px.bar(df_filtered_26000_32000, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (26000-32000)')

# # Plot the third bar chart
# df_filtered_36000_36200 = df_filtered[df_filtered['District'].between(36000, 36200)]
# fig2_36000_36200 = px.bar(df_filtered_36000_36200, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (36000-36200)')

# # Plot the fourth bar chart
# df_filtered_41000_50000 = df_filtered[df_filtered['District'].between(41000, 50000)]
# fig2_41000_50000 = px.bar(df_filtered_41000_50000, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (41000-50000)')

@st.cache_data
def preprocess_data(data):
    df = data.copy()
    df = df.sample(frac=0.001)
    df['TransAmt'] = df['TransAmt'].astype(float)

    # compare the prices of apartments on different floors
    floor_prices = df.groupby(['Apartment', 'Floor'])['Price'].mean().reset_index()

    # visualize the differences using a bar chart
    fig = px.bar(floor_prices, x='Floor', y='TransAmt', color='Apartment', barmode='group')

    return fig

fig = preprocess_data(df) 

# Use Streamlit to display the graph
st.write(fig)


@st.cache_data
def preprocess_data():
    df['TransAmt'] = df['TransAmt'].astype(float)
    # compare the prices of apartments on different floors
    floor_prices = df.groupby(['Floor'])['TransAmt'].mean().reset_index()

    # visualize the differences using a bar chart
    fig = px.bar(floor_prices, x='Floor', y='TransAmt')

    return fig

fig = preprocess_data() 

# Use Streamlit to display the graph
st.write(fig)

add_selectbox = st.sidebar.selectbox(
    'How would you like to be contacted?',
    ('Email', 'Home phone', 'Mobile phone')
)

st.map(df)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly
st.set_option('deprecation.showfileUploaderEncoding', False) #to run streamlit forever and dynamically refresh when source code is updated.
from google.oauth2 import service_account
from google.cloud import storage

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = storage.Client(credentials=credentials)

# Retrieve file contents.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def read_file(bucket_name, file_path):
    bucket = client.bucket(bucket_name)
    content = bucket.blob(file_path).download_as_string().decode("utf-8")
    return content

bucket_name = "streamlit-bucket"
file_path = "myfile.csv"

content = read_file(bucket_name, file_path)
#---------------------------------------------------------------------------------------------------
# Print results.
for line in content.strip().split("\n"):
    name, pet = line.split(",")
    st.write(f"{name} has a :{pet}:")
#Data Types for each column
dtypes = {'RegionCode': int,
          'City': str ,'District': str, 'Neighbourhood': str,'remainingAddr': str, 
          'latitude': float,'longitude': float,'Apartment': str,'postalcode': str,
          'placeId': str,'Lot':str, #TradingDay: datetime
          'FloorArea': float,'Floor': int,'YrBuilt': int,'TransAmt': float,'KRAddr': str}

#Import data
df = pd.read_csv('cleandata.csv',sep=',', dtype = dtypes, parse_dates=['TradingDay'], on_bad_lines = 'warn')
df['latitude'] = df['latitude'].astype(float)
df['longitude'] = df['longitude'].astype(float)
originalrow_count = len(df.index)
df = df.dropna(subset=['City', 'latitude', 'longitude', 'TransAmt','TradingDay']) #Drop record if cols City, latitude, longitude, TransAmt, or TradingDay is None (any) 
print(f"Dropped {originalrow_count-len(df.index)} records.")
df.info()

print(df.head(5)) #example data

#STREAMLIT
st.write("Dashboard to view South Korea apartment sales history")
#st.write(df) #make this chunky, too large
#------------------------------------------GRAPHS START HERE----------------------------------------------------
#1. naming format: type_what it shows_variable ordered by 
data_column = st.selectbox("Select data column", df.columns)
group_column = st.selectbox("Select grouping column", df.columns)
df_grouped = df.groupby(group_column)[data_column].sum().reset_index()
fig = px.bar(df_grouped, x=group_column, y=data_column)
st.plotly_chart(fig)


#LINE GRAPH, see price trend over time, compare median and mean
df['TradingDay'] = pd.to_datetime(df['TradingDay'], format='%Y/%m/%d')
# group by the TradingDay column and calculate the mean and median of the Price column
df_grouped_month = df.groupby(pd.Grouper(key='TradingDay', freq='M'))['TransAmt'].agg(['median', 'mean']).reset_index()
# convert the TradingDay column to the desired format
df_grouped_month['TradingDay'] = df_grouped_month['TradingDay'].dt.strftime('%B/%y')
line_avgmedprice_by_month = px.line(df_grouped_month, x='TradingDay', y=['median', 'mean'])
line_avgmedprice_by_month.update_traces(mode='markers+lines')
st.plotly_chart(line_avgmedprice_by_month)


st.write("Price range of Apartments")
ordersOfMag_list = ["", "Thousand", "Million", "Billion", "Trillion"]
for i in range(4,-1,-1):
    orderOfMag = 1000**i
    if (min := df['TransAmt'].min() / orderOfMag) > 0:
        min = str(min) + " " + ordersOfMag_list[i]
        break
for i in range(4,-1,-1):
    orderOfMag = 1000**i
    if (max := df['TransAmt'].max() / orderOfMag) > 0:
        max = str(max) + " " + ordersOfMag_list[i]
        break
min + " - " + max

#Show distribution of apartment sales
#Create histogram
hist_apartmentsales_by_price = plotly.graph_objs.Figure(data=[plotly.graph_objs.Histogram(x=df['TransAmt'], nbinsx=5000)])
hist_apartmentsales_by_price.update_layout(
    title='Distribution of Apartment Sales',
    xaxis_title='Value',
    yaxis_title='Frequency',
    bargap=0.1
)
st.plotly_chart(hist_apartmentsales_by_price)

#Calculate the cost per floor area (m^2)
df['cost_per_area'] = df['TransAmt'] / df['FloorArea']
#Plot the graph
fig_cost_per_area_by_district = px.violin(df, x='District', y='cost_per_area', title="Cost per Area m^2 in different districts") 
st.plotly_chart(fig_cost_per_area_by_district)


#order by district, cost per area, avg cost
# group by the TradingDay column and calculate the mean and median of the Price column
df_grouped_district = df.groupby(pd.Grouper(key =['City', "District"]))['TransAmt'].agg(['median', 'mean', "sum"]).reset_index()
df_grouped_district = df.groupby(pd.Grouper(key =['City', "District"]))['cost_per_area'].agg(['median', 'mean', "sum"]).reset_index()


bar_avgmedprice_district = px.bar(df_grouped_district, x='District', y=['TransAmt', 'cost_per_area']['median', 'mean'])
bar_sumprice_district = px.bar(df_grouped_district, x='District', y=['TransAmt', 'cost_per_area']['sum'])
st.plotly_chart()
# show chart

# # Plot the first bar chart
# df_filtered_11000_12000 = df_filtered[df_filtered['District'].between(11000,12000)]
# fig2_11000_12000 = px.bar(df_filtered_11000_12000, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (11000-12000)')

# # Plot the second bar chart
# df_filtered_26000_32000 = df_filtered[df_filtered['District'].between(26000, 32000)]
# fig2_26000_32000 = px.bar(df_filtered_26000_32000, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (26000-32000)')

# # Plot the third bar chart
# df_filtered_36000_36200 = df_filtered[df_filtered['District'].between(36000, 36200)]
# fig2_36000_36200 = px.bar(df_filtered_36000_36200, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (36000-36200)')

# # Plot the fourth bar chart
# df_filtered_41000_50000 = df_filtered[df_filtered['District'].between(41000, 50000)]
# fig2_41000_50000 = px.bar(df_filtered_41000_50000, x='District', y='price_per_area', color='price_per_area', title='Price per Floor Area vs District Number (41000-50000)')

@st.cache_data
def preprocess_data(data):
    df = data.copy()
    df = df.sample(frac=0.001)
    df['TransAmt'] = df['TransAmt'].astype(float)

    # compare the prices of apartments on different floors
    floor_prices = df.groupby(['Apartment', 'Floor'])['Price'].mean().reset_index()

    # visualize the differences using a bar chart
    fig = px.bar(floor_prices, x='Floor', y='TransAmt', color='Apartment', barmode='group')

    return fig

fig = preprocess_data(df) 

# Use Streamlit to display the graph
st.write(fig)


@st.cache_data
def preprocess_data():
    df['TransAmt'] = df['TransAmt'].astype(float)
    # compare the prices of apartments on different floors
    floor_prices = df.groupby(['Floor'])['TransAmt'].mean().reset_index()

    # visualize the differences using a bar chart
    fig = px.bar(floor_prices, x='Floor', y='TransAmt')

    return fig

fig = preprocess_data() 

# Use Streamlit to display the graph
st.write(fig)

add_selectbox = st.sidebar.selectbox(
    'How would you like to be contacted?',
    ('Email', 'Home phone', 'Mobile phone')
)

st.map(df)







with st.echo(code_location='below'):
    total_points = st.slider("Number of points in spiral", 1, 5000, 2000)
    num_turns = st.slider("Number of turns in spiral", 1, 100, 9)

    Point = namedtuple('Point', 'x y')
    data = []

    points_per_turn = total_points / num_turns

    for curr_point_num in range(total_points):
        curr_turn, i = divmod(curr_point_num, points_per_turn)
        angle = (curr_turn + 1) * 2 * math.pi * i / points_per_turn
        radius = curr_point_num / total_points
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        data.append(Point(x, y))

    st.altair_chart(alt.Chart(pd.DataFrame(data), height=500, width=500)
        .mark_circle(color='#0068c9', opacity=0.5)
        .encode(x='x:Q', y='y:Q'))
