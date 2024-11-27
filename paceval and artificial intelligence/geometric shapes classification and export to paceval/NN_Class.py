import numpy as np
import scipy.special

class NeuralNetwork:
    def activation_function_without_lambda(self, x):
        return scipy.special.expit(x)
    
    def inverse_activation_function_without_lambda(self, x):
        return scipy.special.logit(x)
    
    def __init__(self, inputnodes, hiddennodes, outputnodes, learningrate) -> None:
        self.inputnodes = inputnodes
        self.hiddennodes = hiddennodes
        self.outputnodes = outputnodes
        self.learningrate = learningrate
        #weight matrices, wih (weights input to hidden layer) & who
        self.wih = np.random.normal(0.0, pow(self.hiddennodes, -0.5), (self.hiddennodes, self.inputnodes))
        self.who = np.random.normal(0.0, pow(self.outputnodes, -0.5), (self.outputnodes, self.hiddennodes))
        #acivation function
        self.activation_function = self.activation_function_without_lambda
        self.inverse_activation_function = self.inverse_activation_function_without_lambda
        
    def train(self, x_list, y_list):
        #convert input list to 2d array
        inputs = np.array(x_list, ndmin=2).T
        targets = np.array(y_list, ndmin=2).T
        
        #calculate input to hidden layer
        hidden_inputs = np.dot(self.wih, inputs)
        #calculate hidden output and input to output layer
        hidden_outputs = self.activation_function(hidden_inputs)
        output_inputs = np.dot(self.who, hidden_outputs)
        #calculate final outputs
        final_outputs = self.activation_function(output_inputs)
        #calculate error
        output_errors = targets - final_outputs
        #calculate hidden layer errors (output errors split by weights)
        hidden_errors = np.dot(self.who.T, output_errors)
        #update weights from hidden to output layer
        self.who += self.learningrate * np.dot((output_errors * final_outputs * (1.0 - final_outputs)), np.transpose(hidden_outputs))
        #update weights from input to hidden layer
        self.wih += self.learningrate * np.dot((hidden_errors * hidden_outputs * (1.0 - hidden_outputs)), np.transpose(inputs))
    
    def query(self, x_list):
        inputs = np.array(x_list, ndmin=2).T
        
        #calculate input to hidden layer
        hidden_inputs = np.dot(self.wih, inputs)
        #calculate inputs to output layer
        hidden_outputs = self.activation_function(hidden_inputs)
        output_inputs = np.dot(self.who, hidden_outputs)
        final_outputs = self.activation_function(output_inputs)
        return final_outputs
    
    # backquery the neural network
    # we'll use the same termnimology to each item, 
    # eg target are the values at the right of the network, albeit used as input
    # eg hidden_output is the signal to the right of the middle nodes
    def backquery(self, targets_list):
        # transpose the targets list to a vertical array
        final_outputs = np.array(targets_list, ndmin=2).T
        
        # calculate the signal into the final output layer
        final_inputs = self.inverse_activation_function(final_outputs)

        # calculate the signal out of the hidden layer
        hidden_outputs = np.dot(self.who.T, final_inputs)
        # scale them back to 0.01 to .99
        hidden_outputs -= np.min(hidden_outputs)
        hidden_outputs /= np.max(hidden_outputs)
        hidden_outputs *= 0.98
        hidden_outputs += 0.01
        
        # calculate the signal into the hidden layer
        hidden_inputs = self.inverse_activation_function(hidden_outputs)
        
        # calculate the signal out of the input layer
        inputs = np.dot(self.wih.T, hidden_inputs)
        # scale them back to 0.01 to .99
        inputs -= np.min(inputs)
        inputs /= np.max(inputs)
        inputs *= 0.98
        inputs += 0.01
        
        return inputs
    
    def save_weights(self):
        # Path to save the weights
        file_path1 = "model_weights/weights_layer1.npy"
        file_path2 = "model_weights/weights_layer2.npy"

        # Save the weights as a .npy file
        np.save(file_path1, self.wih)
        np.save(file_path2, self.who)
        