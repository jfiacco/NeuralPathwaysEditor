# Neural Pathways Editor

A work-in-progress viewer for functional components within a neural model.

Currently the best paper to cite for this is:

```
@inproceedings{fiacco-etal-2019-deep,
    title = "Deep Neural Model Inspection and Comparison via Functional Neuron Pathways",
    author = "Fiacco, James  and
      Choudhary, Samridhi  and
      Rose, Carolyn",
    booktitle = "Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics",
    month = jul,
    year = "2019",
    address = "Florence, Italy",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/P19-1575",
    doi = "10.18653/v1/P19-1575",
    pages = "5754--5764",
    abstract = "We introduce a general method for the interpretation and comparison of neural models. The method is used to factor a complex neural model into its functional components, which are comprised of sets of co-firing neurons that cut across layers of the network architecture, and which we call neural pathways. The function of these pathways can be understood by identifying correlated task level and linguistic heuristics in such a way that this knowledge acts as a lens for approximating what the network has learned to apply to its intended task. As a case study for investigating the utility of these pathways, we present an examination of pathways identified in models trained for two standard tasks, namely Named Entity Recognition and Recognizing Textual Entailment.",
}
```

## User Guide

This tool can be used to quickly analyze small to medium sized neural networks where one has extracted the activations of the network and has a table of attributes. This guide is structured to navigate users through the tool's functionalities, providing practical considerations for the four phases of the analysis process: choosing attributes, determining the number of pathways, determining pathway correlations, and performing a qualitative analysis.

In this initial phase, the focus is on selecting attributes that are potentially significant for the model's decision-making process. This selection is crucial as it influences the subsequent analysis of neural pathways. Attributes can range from input features to more abstract model-specific characteristics. The choice of attributes should be guided by the specific objectives of the analysis and the theoretical underpinnings of the model.

The next phase involves setting a practical limit on the number of neural pathways to be analyzed. The decision is a balance between computational feasibility and the comprehensiveness of the analysis. A higher number of pathways might provide a more detailed picture but at the cost of increased complexity.

In the main analysis phase, the tool helps to uncover how the identified pathways correlate with the chosen attributes. This analysis is pivotal in understanding the interplay between different components of the model. Correlation analysis can reveal insights such as dependencies, redundancies, or unique contributions of specific pathways to the model's behavior.

The final phase involves a qualitative analysis, where the correlations from the previous phases are interpreted and contextualized by projecting them onto the data. This phase allows for a deeper understanding of the model, going beyond mere statistical relationships. It involves examining the pathways in the context of the analysis data to provide an intuition for the findings.

Throughout this guide, we will provide detailed walkthroughs, accompanied by screenshots from the tool, to illustrate each step of the process. By the end of this guide, users will be equipped with a thorough understanding of how to leverage this tool to analyze neural pathways in a range of models, leading to more informed interpretations and potentially more robust model development.

### Choosing Attributes

This section of the user guide provides instructions on how to load your analysis dataset into the Pathways Explorer Tool and select appropriate attributes for your analysis. The process involves importing a CSV file of attributes and considerations for choosing relevant attributes.

**Step 1 - Preparing Your CSV File:**
Before you begin, ensure that your CSV file is properly formatted. Each row in the file should represent a distinct data instance in your analysis dataset, and each column should correspond to either features of your model or attributes that may be correlated with the neural pathways. It is important that this data is clean and accurately represents the variables of interest for your analysis.

**Step 2 - Loading the CSV File into the Tool:**

1. _Open the Pathways Analysis Tool_: Launch the application and navigate to the _Attributes_ tab.
2. _Import the CSV File_: Look for the option to `Select File'. Click on this option and navigate to the location of your CSV file on your computer.
3. _Select and Open the File_: Choose the CSV file you prepared and open it. The tool will process the file and load the data.

**Step 3 - Confirm the Table of Attributes:**
Once the CSV file is loaded, the tool will display the table of attributes. This table will show all the columns from your CSV file, representing the features and attributes of your analysis dataset. Verify that this table is correct.

**Tip - Choosing Attributes:**
Choosing the right attributes is crucial as it determines the perspective from which you will analyze the model. Attributes should be closely related to the specific task your model is designed to perform and should ideally be independent to provide a clear and unbiased view of the model's behavior.

Following these steps will successfully load your analysis dataset into the Pathways Explorer Tool and set the stage for a comprehensive analysis of neural pathways based on the attributes relevant to your specific research or application scenario.

### Determining the Number of Pathways

This section of the user guide explains how to extract neural pathways from neuron activations using the Pathways Analysis Tool. The process involves loading neuron activations from a JSON file and choosing the appropriate method and parameters for pathway extraction.

**Step 1 - Prepare Activation JSON File:**
The neuron activations should be in a JSON file with the following format:

```
{"<NAME OF LAYER/NEURON SET>": 
    [[<ACTIVATIONS FOR DATA INSTANCE 0>], ..., 
     [<ACTIVATIONS FOR DATA INSTANCE N>]], ...}
```

Each key in the JSON object represents a layer or set of neurons, and the associated value is a list of activation values for each data instance.

**Step 2 - Loading Neuron Activations:**
1. _Navigate to the Extract Tab_: Look for a tab or section labeled _Extract_. Click on this tab to navigate to the pathway extraction section of the tool.
2. _Load the JSON File_: In the _Extract_ tab, find the option to `Select File'. Select this option and navigate to your prepared JSON file.
3. _Confirm the File Selection_: Choose the JSON file and confirm to upload it. The tool will then process and display the neuron activations.

**Step 3 - Choosing the Pathway Extraction Method:**
Select the pathway extraction method with the dropdown menu. The default method for pathway extraction is Factor Analysis. An alternative option available is Principal Component Analysis (PCA). Choose the method that best suits your analysis needs; factor analysis generally provides better quality pathways, though PCA is often faster for larger datasets or models.

**Step 4 - Setting the Target Percent of Variance:**
1. _Determine the Target Percent of Variance_: Decide on the percentage of variance that should be explained by the pathways. This is a crucial decision, as it affects the complexity and quantity of the pathways extracted. A higher percentage means less information loss but results in more complex and numerous pathways.
2. _Input the Target Percent of Variance:_ In the tool, locate the option to set the target percent of variance. Enter the value you have determined based on your analysis needs.

**Tip - Determining the Number of Pathways**
As a guideline, it is recommended to aim for a percent variance that yields approximately one-tenth the number of pathways as there are neurons in your model. This ratio is suggested as a starting point and can be adjusted based on the specific requirements of your task.

**Step 4 - Extracting Pathways:**
Once all settings are confirmed, proceed to extract the pathways by clicking the 'Extract Pathways' button. The tool will process the neuron activations using your specified method and variance target, resulting in a set of neural pathways for further analysis. The number of pathways and each of their percent variance explained will be displayed above the `Extract' button. The percent variance explained and the method for extraction can be changed after extraction, but you must use the `Extract' button to extract pathways with the new settings.

### Determining Pathway Correlations

This section provides instructions on how to analyze the correlations between extracted pathways and loaded attributes using the Pathways Analysis Tool. The process involves selecting attributes for correlation computations, choosing a correlation method, and interpreting the results through graphical representations.

**Step 1 - Navigating to the Pathways Tab:**
1. _Verify Attributes and Pathways_: Before proceeding with this section, attributes must be loaded and pathways must be extracted.
2. _Locate the Pathways Tab_: Look for a tab or section labeled _Pathways_. Click on this tab to access the correlation analysis section.

**Step 2 - Selecting Attributes for Correlation:**
1. _Review the Attributes Table_: In the top left section under the Pathways tab, you will find a table populated with attributes and features from the _Attributes_ tab.
2. _Toggle Attributes_: Next to each attribute in the table, there is a checkbox. By toggling the checkbox, you can include or exclude that attribute from the correlation computations.
3. _Confirm Your Selections_: Ensure that checkboxes are checked for all attributes you wish to analyze, and unchecked for those you want to exclude.

**Step 3 - Choosing the Correlation Method:**
By default, the tool uses Pearson's R value for correlation. An alternative option available is Logistic Regression, where correlations reflect the weights learned by a logistic regression model trained to predict the attribute class with the pathways as inputs. For most cases, the default Pearson's R value is recommended. However, choose the method that aligns best with your analysis needs.

**Step 4 - Analyzing the Correlations:**
1. _Initiate the Analysis_: Click on the `Analyze' button. The tool will compute correlations between each attribute and each pathway.
2. _View the Results_: The correlations will be displayed in bar graphs, with each graph representing an attribute. Within each graph, individual bars represent the correlation of a pathway with that attribute.

**Tip - Interpreting the Bars**: Bars that represent correlation above a certain threshold are highlighted for convenience. In many practical scenarios, a Pearson's correlation greater than 0.3 is generally indicative of a pattern that is qualitatively discernible in the data. The graphical representation of correlations provides a clear and intuitive understanding of how different pathways relate to each attribute. The highlight feature on the bars assists in quickly identifying significant correlations, streamlining the process of pinpointing relevant pathways for further investigation.

### Qualitative Analysis

This section of the user guide describes the process of conducting a qualitative analysis on the pathways using the Pathways Analysis Tool. This analysis involves interacting with the correlation bar graphs to explore the data instances most associated with specific pathways and to understand the connection between these pathways and attributes.

**Step 1 - Interacting with the Correlation Bar Graphs:**
1. _Locate the Correlation Bar Graphs_: Ensure you are in the _Pathways_ tab where the correlation bar graphs are displayed following your analysis.
2. _Select a Pathway for Analysis_: Click on one of the bars in the correlation bar graphs. The bar you select represents a specific pathway and its correlation with an attribute.

Upon clicking, the selected bar will be highlighted, indicating it is the focus of your qualitative analysis.

**Step 2 - Viewing Data Instances Related to the Selected Pathway:**
1. _Examine the Bottom Left Table_: Once a bar is selected, look at the table located in the bottom left of the window. This table will automatically populate with data instances.
2. _Review the Displayed Data_: The data instances shown are those that most activate the pathway represented by the clicked-on bar.
3. _Note the Attribute Labels_: Alongside each data instance, the label of the attribute for that instance, corresponding to the attribute of the selected graph, will also be displayed.

**Tip - Customizing the Data Display:**
1. _Choose a Column from the Attribute Table_: For tasks involving textual data, it is recommended to display the raw text of the data instances. Select a column from the attribute table that you wish to view via the dropdown menu.
2. _Adjust the Number of Displayed Instances_: The tool allows you to change the number of data instances shown in the table. Depending on the complexity of the task and the strength of the correlation, you may need to adjust this number. More instances can help in discerning patterns, especially in cases of weaker correlations or more complex tasks.

**Step 3 - Verifying Connections Between Pathways and Attributes:**
This qualitative analysis provides an opportunity to validate the quantitative findings from the correlation analysis and to gain a deeper, more nuanced understanding of the relationships within the model.
1. _Analyze the Data_: Use the information in the table to observe and analyze how the most activated data instances correlate with the selected pathway and its associated attribute.
2. _Confirm Relationships_: This step allows you to quickly verify the connections between specific pathways and attributes. Look for patterns or trends in the data that support the correlation indicated by the bar graph.
