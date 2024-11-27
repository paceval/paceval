import random
import numpy as np
from collections import defaultdict
import pandas as pd
from tqdm import tqdm
import math

class Model_Evaluator:
    def __init__(self, intensity, query_the_model, forecast_length) -> None:
        self.intensity = intensity
        self.query_the_model = query_the_model
        self.forecast_length = forecast_length
        
        # Generate samples & scores
        self.all_oem_forecasts = self.create_random_forecasts(int(500*self.intensity), forecast_length, 0.25)
        self.all_oem_scores = [self.query_the_model(forecast) for forecast in self.all_oem_forecasts]
        
        self.all_supplier_forecasts = []
        self.all_supplier_scores = []
        for oem_forecast in tqdm(self.all_oem_forecasts):
            new_forecasts = self.create_supplier_forecasts(int(50*self.intensity), oem_forecast)
            self.all_supplier_forecasts.append(new_forecasts)
            #calculate the scores
            new_scores_all_deltas = {}
            for delta, forecasts in new_forecasts.items():
                scores_one_delta = []
                for forecast in forecasts:
                    scores_one_delta.append(self.query_the_model(forecast))
                new_scores_all_deltas[delta] = scores_one_delta
            self.all_supplier_scores.append(new_scores_all_deltas)
        
        #calculate the differences & the average differences between the scores of the oems and the suppliers
        self.all_supplier_scores_diff = []
        
        for i, oem_score in enumerate(self.all_oem_scores):
            new_scores_diff_all_deltas = {}
            for delta, supplier_scores in self.all_supplier_scores[i].items():
                new_scores_one_delta = []
                for score in supplier_scores:
                    new_scores_one_delta.append(abs(score - oem_score))
                new_scores_diff_all_deltas[delta] = new_scores_one_delta
            self.all_supplier_scores_diff.append(new_scores_diff_all_deltas)
        
        #save the all_supplier_scores_diff in a dataframe for visualization
        delta_data = [[] for _ in range(len(self.all_supplier_scores_diff[0]))]
        for supplier_scores_diff in self.all_supplier_scores_diff:
            for i2, (delta, diff) in enumerate(supplier_scores_diff.items()):
                    for element in diff: #to flatten it out 
                        delta_data[i2].append(element)
        
        index = [f"{delta}" for delta in self.all_supplier_scores_diff[0].keys()]
        self.df = pd.DataFrame(data=delta_data, index=index)
        self.df = pd.concat([pd.DataFrame({"data": [None]}, index=['0.0']), self.df])
        
        #function to calculate the total of the difference between every element of the inputs
    def calculate_scores_again(self):
        self.all_oem_scores = [self.query_the_model(forecast) for forecast in self.all_oem_forecasts]
        self.all_supplier_scores = []
        
        for i, oem_forecast in enumerate(self.all_oem_forecasts):
            supplier_forecasts = self.all_supplier_forecasts[i]
            #calculate the scores
            new_scores_all_deltas = {}
            for delta, forecasts in supplier_forecasts.items():
                scores_one_delta = []
                for forecast in forecasts:
                    scores_one_delta.append(self.query_the_model(forecast))
                new_scores_all_deltas[delta] = scores_one_delta
            self.all_supplier_scores.append(new_scores_all_deltas)
        
        #calculate the differences & the average differences between the scores of the oems and the suppliers
        self.all_supplier_scores_diff = []
        
        for i, oem_score in enumerate(self.all_oem_scores):
            new_scores_diff_all_deltas = {}
            for delta, supplier_scores in self.all_supplier_scores[i].items():
                new_scores_one_delta = []
                for score in supplier_scores:
                    new_scores_one_delta.append(abs(score - oem_score))
                new_scores_diff_all_deltas[delta] = new_scores_one_delta
            self.all_supplier_scores_diff.append(new_scores_diff_all_deltas)
        
        #save the all_supplier_scores_diff in a dataframe for visualization
        self.df = None
        delta_data = [[] for _ in range(len(self.all_supplier_scores_diff[0]))]
        for supplier_scores_diff in self.all_supplier_scores_diff:
            for i2, (delta, diff) in enumerate(supplier_scores_diff.items()):
                    for element in diff: #to flatten it out 
                        delta_data[i2].append(element)
        
        index = [f"{delta}" for delta in self.all_supplier_scores_diff[0].keys()]
        self.df = pd.DataFrame(data=delta_data, index=index)
        self.df = pd.concat([pd.DataFrame({"data": [None]}, index=['0.0']), self.df])
        return self.df
    
    def change_query_model_function(self, new_function):
        self.query_the_model = new_function
        
    def calculate_total_diff(self, input1, input2):
        return sum(np.abs(np.array(input1) - np.array(input2)))

    def create_random_forecasts(self, amount: int, forecast_length, standard_deviation):
        all_forecasts = []
        for i1 in range(amount):
            forecast = [0 for i in range(forecast_length)]
            # calculate how many weeks should have a different forecast than 0
            change_weeks = random.randint(5, 15)
            # calculate change_weeks many random indices to change the forecast at those indices
            random_integers = [random.randint(0, forecast_length-1) for i2 in range(change_weeks)]
            # change the forecast at the indices with random choices out of the possible values
            for i3 in range(change_weeks):
                while True:
                    forecast[random_integers[i3]] = np.random.normal(0, standard_deviation, 1)[0]
                    if forecast[random_integers[i3]] < 0.8 and forecast[random_integers[i3]] > -0.8:
                        break
            all_forecasts.append(forecast)
        return all_forecasts

    def create_delta_forecasts(self, amount: int, delta, oem_forecast):
        """
        creates supplier forecasts with a given total difference (delta) in the forecast of the oem and the supplier
        the function choose random indices to change the forecast at to reach the given delta
        """
        all_suplier_forecasts = []
        for i in range(amount):
            #create a while loop to check if the calculation was correct and only then append the forecast
            # # create a copy of the oem_forecast
            supplier_forecast = np.array(oem_forecast.copy())
            while True:
                # calculate the difference that is still missing
                missing_delta = delta - self.calculate_total_diff(supplier_forecast, oem_forecast)
                #if the supplier forecast has enough difference: break
                if missing_delta <= 0.1 and missing_delta >= -0.1:
                    break
                #else change a random value to create more difference
                #randomize the index you want to change a value at
                index = random.randint(0, len(oem_forecast)-1)
                #calculate the new value
                old_value = supplier_forecast[index]
                
                while True:
                    new_value = np.clip(np.random.normal(0, 0.5, 1)[0], -1, 1) #random value with normal distribution with mean 0 and sd of 0.5 is clipped to be within -1 and 1
                    #make sure we don't shoot above our goal
                    if abs(new_value - old_value)<=missing_delta:
                        break
                #change the value in the supplier forecast
                supplier_forecast[index] = new_value
                    
            all_suplier_forecasts.append(supplier_forecast)
        return all_suplier_forecasts
    
    #generate multiple supplier forecasts for every oem
    def create_supplier_forecasts(self, amount_per_change: int, oem_forecast, max_delta=15):
        """
        this function will general multiple forecasts per pre defined delta/difference in the forecast.
        It will generate forecasts for a total difference of the prediction values in the forecasts of 0.1 - 15(max_delta) (ascending in steps of 0.1 -> 150 Different differences/deltas)
        """
        
        supplier_forecasts = {}
        all_deltas = [x/10 for x in range(1, max_delta*10+1)]
        for delta in all_deltas:
            forecasts = self.create_delta_forecasts(amount_per_change, delta, oem_forecast)
            supplier_forecasts[delta] = forecasts
        return supplier_forecasts
    
    def calculate_interval(self, forecasts_in_interval=0.8):
        """
        calculates a range in which 80 (or forecasts_in_interval*100) Percent of the Forecasts are
        """
        # Flatten the list of dictionaries into a single list of numeric values
        all_values = []
        for scores_diff in self.all_supplier_scores_diff:
            for values in scores_diff.values():
                all_values.extend(values)
        
        all_values_series = pd.Series(all_values)
        
        upper_bound = all_values_series.quantile(forecasts_in_interval)
        lower_bound = all_values_series.min()
        # Create the interval
        interval = (lower_bound, upper_bound)
        return interval
    
    def apply_normalization(self, normalize_value):
        pass 
        
    def evaluate_model(self, output_type='median', scale_range=[], libary='plt'):
        """
        intensity: float between 0 and 1: influences how many samples should be generated for testing. the more samples the more accurate is the result
        query_the_model: a function that queries the model, returns the result/score and takes a forecast as input
        """
        #imports
        import plotly.express as px
        import matplotlib.pyplot as plt
        # Clear any existing plots
        plt.clf()
        plt.close()
        #visualize
        # we will switch to only using matplotlib, as plotly plots tend to turn into white screens when the RAM gets too full
        if output_type == 'avg':
            # Calculate mean for each row
            self.df['mean'] = self.df.mean(axis=1)
            print(f"Classification at 0.1: {self.df['mean']['0.1']}")
            print(f"Classification at 3.0: {self.df['mean']['3.0']}")
            print(f"Classification at 8.0: {self.df['mean']['8.0']}")
            print(f"Classification at 15.0: {self.df['mean']['15.0']}")
            # Create the plot
            plt.figure(figsize=(20, 10))
            plt.scatter(self.df.index, self.df['mean'], color='b')  # Use 'o' for points and '-' for lines

            # Add labels and title
            plt.xlabel('Manhattan-Distanz der Prognosen von Stufe 1 & Stufe 2', fontsize=14)
            plt.ylabel('Durchschnitt der Differenzen der Scores der Prognosen von Stufe 1 & Stufe 2', fontsize=14)

            # Only show every 10th x beginning at the 10th value (1.0) value for better readability
            plt.xticks(self.df.index[0::10], fontsize=12)
            plt.yticks(fontsize=12)
            # Add grid for better readability
            plt.grid(True)
            plt.xlim(left=0)
            plt.ylim(0, None)
            # Show the plot
            plt.show()

        elif output_type == 'median':
            # Calculate mean for each row
            self.df['median'] = self.df.median(axis=1)
            print(f"Classification at 0.1: {self.df['median']['0.1']}")
            print(f"Classification at 3.0: {self.df['median']['3.0']}")
            print(f"Classification at 8.0: {self.df['median']['8.0']}")
            print(f"Classification at 15.0: {self.df['median']['15.0']}")
            # Create the plot
            plt.figure(figsize=(20, 10))
            plt.scatter(self.df.index, self.df['median'], color='b')  # Use 'o' for points and '-' for lines

            # Add labels and title
            plt.xlabel('Manhattan-Distanz der Prognosen von Stufe 1 & Stufe 2', fontsize=14)
            plt.ylabel('Median der Differenzen der Scores der Prognosen von Stufe 1 & Stufe 2', fontsize=14)

            # Only show every 10th x beginning at the 10th value (1.0) value for better readability
            plt.xticks(self.df.index[0::10], fontsize=12)
            plt.yticks(fontsize=12)
            plt.xlim(left=0)
            plt.ylim(0, None)
            # Add grid for better readability
            plt.grid(True)

            # Show the plot
            plt.show()
            
        elif output_type == "std": 
            # Calculate mean and standard deviation for each row
            self.df['mean'] = self.df.mean(axis=1)
            self.df['std'] = self.df.std(axis=1)

            plt.figure(figsize=(12, 8))
            plt.errorbar(self.df.index, self.df['mean'], yerr=self.df['std'], fmt='o', ecolor='red', capsize=5)
            plt.xlabel('Row Index')
            plt.ylabel('Mean Value')
            plt.title('Model Evaluation - Mean and Standard Deviation of Score Difference')
            # Only show every 10th x beginning at the 10th value (1.0) value for better readability
            plt.xticks(self.df.index[0::10])
            plt.xlim(left=0)
            plt.ylim(0, None)
            plt.grid(True)
            plt.show()
            
        elif output_type == "scatter" or output_type == "scatter_log" or output_type == "scatter_tight":
            #convert df to long format
            # Resetting the index to keep the row labels (e.g., 0.2, 0.3) as a column
            df_reset = self.df.reset_index()

            # Melting the DataFrame to a long format
            df_melted = df_reset.melt(id_vars='index', var_name='Delta', value_name='Value')
            
            if libary=="plt":
                # Create the plot
                plt.figure(figsize=(20, 10))
                plt.scatter(df_melted["index"], df_melted['Value'], color='b', s=10)  # Use 'o' for points and '-' for lines
                # Add labels and title
                plt.xlabel('Manhattan-Distanz der Prognosen von Stufe 1 & Stufe 2', fontsize=14)
                plt.ylabel('Differenz der Scores der Prognosen von Stufe 1 & Stufe 2', fontsize=14)
                # Only show every 10th x beginning at the 10th value (1.0) value for better readability
                plt.xticks(self.df.index[0::10], fontsize=12)
                plt.yticks(fontsize=12)
                # Add grid for better readability
                plt.grid(True)
                plt.ylim(0, None)
                if output_type == "scatter_tight":
                    #fig.update_yaxes(range=scale_range)
                    plt.ylim(scale_range)
                plt.xlim(left=0)
                # Show the plot
                plt.show()    

        elif output_type == "heatmap" or output_type == "heatmap_tight":
            #convert df to long format

            # Resetting the index to keep the row labels (e.g., 0.2, 0.3) as a column
            df_reset = self.df.reset_index()

            # Melting the DataFrame to a long format
            df_melted = df_reset.melt(id_vars='index', var_name='Delta', value_name='Value')

            # Rename the 'index' column to something more meaningful, like 'Row'
            df_melted.rename(columns={'index': 'Row'}, inplace=True)
            
            # Create a density heatmap
            fig = px.density_heatmap(df_melted, x='Row', y='Value', z='Value',
                                    nbinsx=50, nbinsy=200,  # Adjust the number of bins for resolution
                                    histfunc='count',  # Aggregation function to count points
                                    color_continuous_scale='Viridis')

            # Customize the heatmap for better readability
            fig.update_layout(
                title="Density Heatmap of Supplier Score Differences",
                xaxis_title="Row Index",
                yaxis_title="Delta",
                coloraxis_colorbar=dict(title="Number of Forecasts")
            )
            if output_type == "heatmap_tight":
                # Set y-axis to logarithmic scale to show more details for points around 0
                fig.update_yaxes(range=scale_range)
            else:
                # Set the y-axis range manually
                fig.update_yaxes(range=[0, 0.002])

            # Show the heatmap
            fig.show()
        else:
            print("wrong output type")

    def visualize_warning_error(self, dataframe: pd.DataFrame, classification_level_lower_bound: str, classification_level_upper_bound: str, type="avg"):
        """
        function to calculate how many forecasts are in a a given range for each row in the dataframe
        this used when giving a warning to the customer that his forecast is either good or bad
        classification_level is the actual total difference in the score between the supplier and the oem at which a classification between warning or no warning is done
        """
        #calculate the score difference/level that the model outputs at that difference in the forecast
        if type=="avg":
            dataframe[type] = dataframe.mean(axis=1)
        elif type=="median":
            dataframe[type] = dataframe.median(axis=1)
        else:
            print("type either has to be avg for mean or median for median")
            return
        try: model_classification_level_lower_bound = dataframe[type][f"{classification_level_lower_bound}"]
        except: model_classification_level_lower_bound = 0.0 # if lower bound is 0.0 for example
        try: model_classification_level_upper_bound = dataframe[type][f"{classification_level_upper_bound}"]
        except: model_classification_level_upper_bound = 10 # if lower bound is 15.0 for example
        #catch an edge case where the vertical line is plotted at 15.5 if classification_level_lower_bound="0.0"
        if classification_level_lower_bound=="0.0": classification_level_lower_bound= 0.0
        #other edge case 
        if classification_level_upper_bound=="15.0": model_classification_level_upper_bound = 10000
        #other edge  case
        if math.isnan(model_classification_level_lower_bound): model_classification_level_lower_bound=0.0
        # Initialize an empty list to store the results
        results_list = []
        #print the classification levels
        print(f"Classification level lower bound: {model_classification_level_lower_bound}")
        print(f"Classification level upper bound: {model_classification_level_upper_bound}")
        # Iterate over each row in the original DataFrame
        for forecast_difference, row_values in dataframe.iterrows():
            # Count how many values in the row are in the given range
            count_classification_level = ((row_values >= model_classification_level_lower_bound) &
                                (row_values < model_classification_level_upper_bound)).sum()
                
            # Append the result to the results list as a dictionary
            results_list.append({
                'Forecast Difference': forecast_difference, 
                'Count Classification Level': count_classification_level/len(row_values)
            })
        
        # Convert the list of dictionaries to a DataFrame
        results_df = pd.DataFrame(results_list)
        # Set the 'Forecast Difference' as the index of the results DataFrame
        results_df.set_index('Forecast Difference', inplace=True)
        #change the value at index 0.0 
        results_df.loc["0.0"]["Count Classification Level"] = None
        #print some values
        print("MH=2.0: ",results_df.loc["2.0"]["Count Classification Level"])
        print("MH=5.5: ",results_df.loc["5.5"]["Count Classification Level"])
        print("MH=8.5: ",results_df.loc["8.5"]["Count Classification Level"])
        print("MH=15.0: ",results_df.loc["15.0"]["Count Classification Level"])
        #plot the results    
        # Create the plot
        import matplotlib.pyplot as plt
        # Clear any existing plots
        plt.clf()
        plt.close()
        plt.figure(figsize=(20, 10))
        plt.plot(results_df.index, results_df['Count Classification Level'], marker='o', linestyle='-', color='b')  # Use 'o' for points and '-' for lines
        # Add labels and title
        plt.xlabel('Manhattan-Distanz der Prognosen von Stufe 1 & Stufe 2', fontsize=14)
        plt.ylabel(f'Anzahl an Prognosen im Intervall der Klassifizierung ({classification_level_lower_bound}, {classification_level_upper_bound})', fontsize=14)
        
        # add a two markers to show in which range we classified
        #make sure that left border is visible at 0.0
        if classification_level_lower_bound == 0.0:
            classification_level_lower_bound = classification_level_lower_bound+0.2
        plt.axvline(x=classification_level_lower_bound, color='red', linestyle='--', linewidth=2.5, label="Classification Level Lower Bound")
        plt.axvline(x=classification_level_upper_bound, color='red', linestyle='--', linewidth=2.5, label="Classification Level Upper Bound")

        # Only show every 10th x beginning at the 0th value (0.0) value for better readability
        plt.xticks(results_df.index[0::10], fontsize=12)
        plt.yticks([0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0], fontsize=12)

        # Add grid for better readability
        plt.grid(True)
        #make sure the 0 on the y-Achses is shown and the x-Achses is anchored to the left
        plt.xlim(left=0)
        plt.ylim(0, None)
        
        plt.show()

        return results_df
    
class Formula_Evaluator:
    def __init__(self, intensity, query_the_formulas, forecast_length) -> None:
        self.intensity = intensity
        self.query_the_formulas = query_the_formulas
        self.forecast_length = forecast_length
        
        # Generate samples & scores
        self.all_oem_forecasts = self.create_random_forecasts(int(500*self.intensity), forecast_length, 0.25)
        self.all_oem_scores = self.query_the_formulas(self.all_oem_forecasts)
        
        self.all_supplier_forecasts = []
        self.all_supplier_scores = []
        for oem_forecast in tqdm(self.all_oem_forecasts):
            amount_per_mh = int(50*self.intensity)
            new_forecasts = self.create_supplier_forecasts(amount_per_mh, oem_forecast)
            self.all_supplier_forecasts.append(new_forecasts)
            #calculate the scores
            new_scores_dict = {}
            new_scores = self.query_the_formulas(np.concatenate(list(new_forecasts.values()), axis=0))#flatten to 2D List
            for i, key in enumerate(new_forecasts.keys()):
                new_scores_dict[key] = new_scores[(i*amount_per_mh):((i+1)*amount_per_mh)]
            self.all_supplier_scores.append(new_scores_dict)
        
        #calculate the differences & the average differences between the scores of the oems and the suppliers
        self.all_supplier_scores_diff = []
        print(self.all_supplier_scores)
        for i, oem_score in enumerate(self.all_oem_scores):
            new_scores_diff_all_deltas = {}
            for delta, supplier_scores in self.all_supplier_scores[i].items():
                new_scores_one_delta = []
                for score in supplier_scores:
                    new_scores_one_delta.append(abs(score - oem_score))
                new_scores_diff_all_deltas[delta] = new_scores_one_delta
            self.all_supplier_scores_diff.append(new_scores_diff_all_deltas)
        
        #save the all_supplier_scores_diff in a dataframe for visualization
        delta_data = [[] for _ in range(len(self.all_supplier_scores_diff[0]))]
        for supplier_scores_diff in self.all_supplier_scores_diff:
            for i2, (delta, diff) in enumerate(supplier_scores_diff.items()):
                    for element in diff: #to flatten it out 
                        delta_data[i2].append(element)
        
        index = [f"{delta}" for delta in self.all_supplier_scores_diff[0].keys()]
        self.df = pd.DataFrame(data=delta_data, index=index)

        #function to calculate the total of the difference between every element of the inputs
    def calculate_scores_again(self):
        self.all_oem_scores = [self.query_the_formulas(forecast) for forecast in self.all_oem_forecasts]
        self.all_supplier_scores = []
        
        for i, oem_forecast in enumerate(self.all_oem_forecasts):
            supplier_forecasts = self.all_supplier_forecasts[i]
            #calculate the scores
            new_scores_all_deltas = {}
            for delta, forecasts in supplier_forecasts.items():
                scores_one_delta = []
                for forecast in forecasts:
                    scores_one_delta.append(self.query_the_formulas(forecast))
                new_scores_all_deltas[delta] = scores_one_delta
            self.all_supplier_scores.append(new_scores_all_deltas)
        
        #calculate the differences & the average differences between the scores of the oems and the suppliers
        self.all_supplier_scores_diff = []
        
        for i, oem_score in enumerate(self.all_oem_scores):
            new_scores_diff_all_deltas = {}
            for delta, supplier_scores in self.all_supplier_scores[i].items():
                new_scores_one_delta = []
                for score in supplier_scores:
                    new_scores_one_delta.append(abs(score - oem_score))
                new_scores_diff_all_deltas[delta] = new_scores_one_delta
            self.all_supplier_scores_diff.append(new_scores_diff_all_deltas)
        
        #save the all_supplier_scores_diff in a dataframe for visualization
        self.df = None
        delta_data = [[] for _ in range(len(self.all_supplier_scores_diff[0]))]
        for supplier_scores_diff in self.all_supplier_scores_diff:
            for i2, (delta, diff) in enumerate(supplier_scores_diff.items()):
                    for element in diff: #to flatten it out 
                        delta_data[i2].append(element)
        
        index = [f"{delta}" for delta in self.all_supplier_scores_diff[0].keys()]
        self.df = pd.DataFrame(data=delta_data, index=index)
        return self.df
    
    def change_query_model_function(self, new_function):
        self.query_the_formulas = new_function
        
    def calculate_total_diff(self, input1, input2):
        return sum(np.abs(np.array(input1) - np.array(input2)))

    def create_random_forecasts(self, amount: int, forecast_length, standard_deviation):
        all_forecasts = []
        for i1 in range(amount):
            forecast = [0 for i in range(forecast_length)]
            # calculate how many weeks should have a different forecast than 0
            change_weeks = random.randint(5, 15)
            # calculate change_weeks many random indices to change the forecast at those indices
            random_integers = [random.randint(0, forecast_length-1) for i2 in range(change_weeks)]
            # change the forecast at the indices with random choices out of the possible values
            for i3 in range(change_weeks):
                while True:
                    forecast[random_integers[i3]] = np.random.normal(0, standard_deviation, 1)[0]
                    if forecast[random_integers[i3]] < 0.8 and forecast[random_integers[i3]] > -0.8:
                        break
            all_forecasts.append(forecast)
        return all_forecasts

    def create_delta_forecasts(self, amount: int, delta, oem_forecast):
        """
        creates supplier forecasts with a given total difference (delta) in the forecast of the oem and the supplier
        the function choose random indices to change the forecast at to reach the given delta
        """
        all_suplier_forecasts = []
        for i in range(amount):
            #create a while loop to check if the calculation was correct and only then append the forecas
            # # create a copy of the oem_forecast
            supplier_forecast = np.array(oem_forecast.copy())
            while True:
                # calculate the difference that is still missing
                missing_delta = delta - self.calculate_total_diff(supplier_forecast, oem_forecast)
                #if the supplier forecast has enough difference: break
                if missing_delta <= 0.1 and missing_delta >= -0.1:
                    break
                #else change a random value to create more difference
                #randomize the index you want to change a value at
                index = random.randint(0, len(oem_forecast)-1)
                #calculate the new value
                old_value = supplier_forecast[index]
                
                while True:
                    new_value = np.clip(np.random.normal(0, 0.5, 1)[0], -1, 1) #random value with normal distribition with mean 0 and sd of 0.5 is clipped to be within -1 and 1
                    #make sure we dont shoot above our goal
                    if abs(new_value - old_value)<=missing_delta:
                        break
                #change the value in the supplier forecast
                supplier_forecast[index] = new_value
                    
            all_suplier_forecasts.append(supplier_forecast)
        return all_suplier_forecasts
    
    #generate multiple supplier forecasts for every oem
    def create_supplier_forecasts(self, amount_per_change: int, oem_forecast, max_delta=15):
        """
        this function will general multiple forecasts per pre defined delta/difference in the forecast.
        It will generate forecasts for a total difference of the prediction values in the forecasts of 0.1 - 15(max_delta) (ascending in steps of 0.1 -> 150 Different differences/deltas)
        """
        
        supplier_forecasts = {}
        all_deltas = [x/10 for x in range(1, max_delta*10+1)]
        for delta in all_deltas:
            forecasts = self.create_delta_forecasts(amount_per_change, delta, oem_forecast)
            supplier_forecasts[delta] = forecasts
        return supplier_forecasts
    
    def calculate_interval(self, forecasts_in_interval=0.8):
        """
        calculates a range in which 80 (or forecasts_in_interval*100) Percent of the Forecasts are
        """
        # Flatten the list of dictionaries into a single list of numeric values
        all_values = []
        for scores_diff in self.all_supplier_scores_diff:
            for values in scores_diff.values():
                all_values.extend(values)
        
        all_values_series = pd.Series(all_values)
        
        upper_bound = all_values_series.quantile(forecasts_in_interval)
        lower_bound = all_values_series.min()
        # Create the interval
        interval = (lower_bound, upper_bound)
        return interval
    
    def apply_normalization(self, normalize_value):
        pass 
        
    def evaluate_model(self, output_type='avg', scale_range=[], libary='plt'):
        """
        intensity: float between 0 and 1: influences how many samples should be generated for testing. the more samples the more accurate is the result
        query_the_formulas: a function that queries the formulas, returns the result/score and takes a forecast as input
        """
        #imports
        import plotly.express as px
        import matplotlib.pyplot as plt
        # Clear any existing plots
        plt.clf()
        plt.close()
        #visualize
        # we will switch to only using matplotlib, as plotly plots tend to turn into white screens when the RAM gets too full
        if output_type == 'avg':
            # Calculate mean for each row
            self.df['mean'] = self.df.mean(axis=1)
            
            # Create the plot
            plt.figure(figsize=(20, 10))
            plt.scatter(self.df.index, self.df['mean'], color='b')  # Use 'o' for points and '-' for lines

            # Add labels and title
            plt.xlabel('Manhattan Distance of OEM & Supplier Forecasts', fontsize=14)
            plt.ylabel('Average Score Difference of OEM & Supplier Forecasts', fontsize=14)
            plt.title('Model Evaluation - Mean Score Difference', fontsize=18)

            # Only show every 10th x beginning at the 10th value (1.0) value for better readability
            plt.xticks(self.df.index[9::10], fontsize=12)
            plt.yticks(fontsize=12)
            # Add grid for better readability
            plt.grid(True)

            # Show the plot
            plt.show()

        elif output_type == 'median':
            # Calculate mean for each row
            self.df['median'] = self.df.median(axis=1)
            
            # Create the plot
            plt.figure(figsize=(10, 6))
            plt.plot(self.df.index, self.df['median'], marker='o', linestyle='-', color='b')  # Use 'o' for points and '-' for lines

            # Add labels and title
            plt.xlabel('Total Difference in Forecast')
            plt.ylabel('Median of Score Difference')
            plt.title('Model Evaluation - Median of Score Difference')

            # Only show every 10th x beginning at the 10th value (1.0) value for better readability
            plt.xticks(self.df.index[9::10])
            
            # Add grid for better readability
            plt.grid(True)

            # Show the plot
            plt.show()
            
        elif output_type == "std": 
            # Calculate mean and standard deviation for each row
            self.df['mean'] = self.df.mean(axis=1)
            self.df['std'] = self.df.std(axis=1)

            plt.figure(figsize=(12, 8))
            plt.errorbar(self.df.index, self.df['mean'], yerr=self.df['std'], fmt='o', ecolor='red', capsize=5)
            plt.xlabel('Row Index')
            plt.ylabel('Mean Value')
            plt.title('Model Evaluation - Mean and Standard Deviation of Score Difference')
            # Only show every 10th x beginning at the 10th value (1.0) value for better readability
            plt.xticks(self.df.index[9::10])
            
            plt.grid(True)
            plt.show()
            
        elif output_type == "scatter" or output_type == "scatter_log" or output_type == "scatter_tight":
            #convert df to long format

            # Resetting the index to keep the row labels (e.g., 0.2, 0.3) as a column
            df_reset = self.df.reset_index()

            # Melting the DataFrame to a long format
            df_melted = df_reset.melt(id_vars='index', var_name='Delta', value_name='Value')
            if libary=="plt":
                # Create the plot
                plt.figure(figsize=(20, 10))
                plt.scatter(df_melted["index"], df_melted['Value'], color='b', s=10)  # Use 'o' for points and '-' for lines
                # Add labels and title
                plt.xlabel('Manhattan Distance of OEM & Supplier Forecasts', fontsize=14)
                plt.ylabel('Score Difference of OEM & Supplier Forecasts', fontsize=14)
                plt.title('Model Evaluation - Score Difference', fontsize=18)
                # Only show every 10th x beginning at the 10th value (1.0) value for better readability
                plt.xticks(self.df.index[9::10], fontsize=12)
                plt.yticks(fontsize=12)
                # Add grid for better readability
                plt.grid(True)
                
                if output_type == "scatter_tight":
                    #fig.update_yaxes(range=scale_range)
                    plt.ylim(scale_range)
                    
                # Show the plot
                plt.show()    

            elif libary=='plotly':
                # Create the scatter plot using Plotly

                fig = px.scatter(df_melted, x='index', y='Value',
                                title='Interactive Scatter Plot of Supplier Score Differences',
                                labels={'index': 'Row Index', 'Value': 'Values'})
                if output_type == "scatter_log":
                    # Set y-axis to logarithmic scale to show more details for points around 0
                    fig.update_yaxes(type="log")
                    
                elif output_type == "scatter_tight":
                    fig.update_yaxes(range=scale_range)
    
                fig.show()

        elif output_type == "heatmap" or output_type == "heatmap_tight":
            #convert df to long format

            # Resetting the index to keep the row labels (e.g., 0.2, 0.3) as a column
            df_reset = self.df.reset_index()

            # Melting the DataFrame to a long format
            df_melted = df_reset.melt(id_vars='index', var_name='Delta', value_name='Value')

            # Rename the 'index' column to something more meaningful, like 'Row'
            df_melted.rename(columns={'index': 'Row'}, inplace=True)
            
            # Create a density heatmap
            fig = px.density_heatmap(df_melted, x='Row', y='Value', z='Value',
                                    nbinsx=50, nbinsy=200,  # Adjust the number of bins for resolution
                                    histfunc='count',  # Aggregation function to count points
                                    color_continuous_scale='Viridis')

            # Customize the heatmap for better readability
            fig.update_layout(
                title="Density Heatmap of Supplier Score Differences",
                xaxis_title="Row Index",
                yaxis_title="Delta",
                coloraxis_colorbar=dict(title="Number of Forecasts")
            )
            if output_type == "heatmap_tight":
                # Set y-axis to logarithmic scale to show more details for points around 0
                fig.update_yaxes(range=scale_range)
            else:
                # Set the y-axis range manually
                fig.update_yaxes(range=[0, 0.002])

            # Show the heatmap
            fig.show()
        else:
            print("wrong output type")

    def visualize_warning_error(self, dataframe: pd.DataFrame, classification_level_lower_bound: str, classification_level_upper_bound: str):
        """
        function to calculate how many forecasts are in a a given range for each row in the dataframe
        this used when giving a warning to the customer that his forecast is either good or bad
        classification_level is the actual total difference in the score between the supplier and the oem at which a classification between warning or no warning is done
        """
        #calculate the score difference/level that the model outputs at that difference in the forecast
        dataframe['avg'] = dataframe.median(axis=1)
        try: model_classification_level_lower_bound = dataframe['avg'][classification_level_lower_bound]
        except: model_classification_level_lower_bound = -10000 # if lower bound is 0.0 for example
        try: model_classification_level_upper_bound = dataframe['avg'][classification_level_upper_bound]
        except: model_classification_level_upper_bound = 10 # if lower bound is 15.0 for example
        #catch an edge case where the vertical line is plotted at 15.5 if classification_level_lower_bound="0.0"
        if classification_level_lower_bound=="0.0": classification_level_lower_bound= 0.0
        #other edge case 
        if classification_level_upper_bound=="15.0": model_classification_level_upper_bound = 10000
        # Initialize an empty list to store the results
        results_list = []

        # Iterate over each row in the original DataFrame
        for forecast_difference, row_values in dataframe.iterrows():
            # Count how many values in the row are in the given range
            count_classification_level = ((row_values >= model_classification_level_lower_bound) &
                                (row_values <= model_classification_level_upper_bound)).sum()
                
            # Append the result to the results list as a dictionary
            results_list.append({
                'Forecast Difference': forecast_difference, 
                'Count Classification Level': count_classification_level/len(row_values)
            })
            
        # Convert the list of dictionaries to a DataFrame
        results_df = pd.DataFrame(results_list)
        # Set the 'Forecast Difference' as the index of the results DataFrame
        results_df.set_index('Forecast Difference', inplace=True)
        #plot the results    
        # Create the plot
        import matplotlib.pyplot as plt
        # Clear any existing plots
        plt.clf()
        plt.close()
        
        plt.figure(figsize=(20, 10))
        plt.plot(results_df.index, results_df['Count Classification Level'], marker='o', linestyle='-', color='b')  # Use 'o' for points and '-' for lines
        # add a two markers to show in which range we classified
        plt.axvline(x=classification_level_lower_bound, color='red', linestyle='--', linewidth=2, label="Classification Level Lower Bound")
        plt.axvline(x=classification_level_upper_bound, color='red', linestyle='--', linewidth=2, label="Classification Level Upper Bound")
        # Add labels and title
        plt.xlabel('Manhattan Distance of OEM & Supplier Forecasts', fontsize=14)
        plt.ylabel(f'Percentage of Forecasts in the classification range ({classification_level_lower_bound}, {classification_level_upper_bound})', fontsize=14)
        plt.title('Model Evaluation - Warning Error', fontsize=18)
        # Only show every 10th x beginning at the 10th value (1.0) value for better readability
        # include 0.0
        plt.xticks(self.df.index[9::10], fontsize=12)
        plt.yticks([0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0], fontsize=12)
        # Add grid for better readability
        plt.grid(True)
        #make sure the 0 on the y-Achses is shown
        plt.ylim(0, 1.1)
        
        plt.show()

        return results_df