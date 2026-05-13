import streamlit as st

#Slider
x = st.sidebar.slider('x')  # 👈 this is a widget
st.write(x, 'squared is', x * x)

#INput
# inp = st.sidebar.text_input("Your name", key="name")
# st.write(inp)


# Checkbox
import numpy as np
import pandas as pd

# if st.sidebar.checkbox('Show dataframe'):
#     chart_data = pd.DataFrame(
#        np.random.randn(5, 3),
#        columns=['a', 'b', 'c'])

#     chart_data

    #Manipulating session_state + plotting
    # if "chart_data" not in st.session_state:
    #     st.session_state.chart_data = chart_data
    # st.header("Choose a datapoint color")
    # color = st.color_picker("Color", "#FF0000")
    # st.divider()
    # st.scatter_chart(st.session_state.chart_data, x="a", y="b", color=color)


#Selectbox
# df = pd.DataFrame({
#     'first column': [1, 2, 3, 4],
#     'second column': [10, 20, 30, 40]
#     })

# option = st.sidebar.selectbox(
#     'Which number do you like best?',
#      df[['second column', 'first column']])

# 'You selected: ', option



plots = [
        'ALL',
        'emission kyto gases',
        'electricity generation mix',
        'final energy industry',
        'final energy residential commercial',
        'final energy transportation',
        'installed electricity capacity',
        'co2 emission by energy supply',
        'emissions by pollutant energy',
        'emissions by pollutant industrial processes',
        'emissions by pollutant waste',
        'total energy by fuel',
        'primary energy mix',
        'trade primary energy volumes',
        'trade secondary energy volumes'
        'resource extraction'
]
show_plots = st.sidebar.checkbox("Show Analytics Plots Options")

if show_plots:
    plot_options = st.sidebar.multiselect(
        'Which plots do you want to draw?',
        plots
    )
    'Selected Plots: ', plot_options



# left_column, right_column = st.columns(2)
# # You can use a column just like st.sidebar:
# left_column.button('Press me!')

# # Or even better, call Streamlit functions inside a "with" block:
# with right_column:
#     chosen = st.radio(
#         'Sorting hat',
#         ("Gryffindor", "Ravenclaw", "Hufflepuff", "Slytherin"))
#     st.write(f"You are in {chosen} house!")


#Show progress
# import time
# 'Starting a long computation...'

# # Add a placeholder
# latest_iteration = st.empty()
# bar = st.progress(0)

# for i in range(100):
#   # Update the progress bar with each iteration.
#   latest_iteration.text(f'Iteration {i+1}')
#   bar.progress(i + 1)
#   time.sleep(0.1)

# '...and now we\'re done!'


# if "df2" not in st.session_state:
#     st.session_state.df2 = pd.DataFrame(np.random.randn(20, 2), columns=["x", "y"])
# st.header("Choose a datapoint color")
# color = st.color_picker("Color2", "#FF0000")
# st.divider()
# st.scatter_chart(st.session_state.df2, x="x", y="y", color=color)
