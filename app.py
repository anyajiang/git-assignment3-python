import openai
from shiny import App, Outputs, req, ui, reactive, render
import os
import clipboard

os.environ["OPENAI_API_KEY"] = "XXXXXX"
os.environ['DEFAULT_PROMPT'] = 'prompt.txt'


AI_content = reactive.Value([])
loaded_text = reactive.Value(None)

app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.h2("Gene Set AI"),
            ui.input_text_area("geneMessage", "Try a geneset query: ", value = "", rows = 5),
            ui.input_slider("temperature", "Temperature (low: focused, high: creative):", min = 0, max = 2, value = 0.7, step = 0.1),
            ui.input_action_button("example", "Example Query"), 
            ui.input_action_button("runQuery", "Run Query"), 
            ui.input_action_button("clear", "Clear")
        ), 
        ui.panel_main(
            ui.input_selectize("model", label = "Select Model", choices = ("gpt-4o", "gpt-4", "gpt-3.5-turbo"), selected = "gpt-4o", multiple = False),
            ui.input_file("file", "Input Prompt File"),
            ui.input_action_button("prompt", "Show Prompt"),
            ui.input_action_button("copy_response", "Copy Response"),
            ui.h3("Response"),
            ui.output_text_verbatim("assistant")
        )
    )
)  


def server(input, output, session):

    @reactive.effect
    @reactive.event(input.example)
    def _(): 
        ui.update_text_area("geneMessage", value = "GNG5, TBX5, ISL1, RBPJ, CTNNB1, NOTCH1, SMAD4, EYA1, BMP10, SOX9, HES1, ENG, MKS1, SIX1, TBX3, HAND2, PIM1, BMPR2")

    @reactive.effect
    @reactive.event(input.clear)
    def _(): 
        ui.update_text_area("geneMessage", value = "")  

        @render.text
        def assistant(): 
            return ""

    @reactive.effect
    @reactive.event(input.prompt)
    def _():
        file_info = req(input.file())
        file_path = file_info[0]['datapath'] 
        with open(file_path, 'r') as f:
            file_content = f.read().strip()
        gene_message = input.geneMessage()
        combined_content = f"{file_content} {gene_message}"

        loaded_text.set(combined_content)

        m = ui.modal(
            ui.pre(combined_content),  
            ui.input_action_button("copy_prompt", "Copy Prompt"),
            title='Prompt',
            easy_close=True
        )
        ui.modal_show(m)

        @reactive.effect
        @reactive.event(input.copy_prompt)
        def _(): 
            text = loaded_text()
            clipboard.copy(text)

    @reactive.effect
    @reactive.event(input.runQuery)
    def _(): 
        prompt_text = loaded_text.get()
        #print("prompt text", prompt_text)
        user_message = input.geneMessage() 

        with ui.Progress() as p: 
            p.set(message = "Generating response using OpenAI")


            assistant_response = openai.chat.completions.create(
                model = input.model(),
                messages=[{"role": "user", "content": prompt_text}, {"role": "user", "content": user_message}],
                temperature = input.temperature()
            )
            response = assistant_response.choices[0].message.content
            #print("assistant response", response)

            @render.text
            def assistant(): 
                return response
            
            AI_content.set(response)

    @reactive.effect
    def _():
        if input.file is None:
            with open(os.getenv("DEFAULT_PROMPT"), 'r') as f:
                text = f.read().strip()
                gene_message = input.geneMessage()
                combined_content = f"{text} {gene_message}"
                loaded_text.set(text)
        else:   
            file_info = req(input.file())
            file_path = file_info[0]['datapath'] 
            with open(file_path, 'r') as f:
                file_content = f.read().strip()
                gene_message = input.geneMessage()
                combined_content = f"{file_content} {gene_message}"

                loaded_text.set(combined_content)

    @reactive.effect
    @reactive.event(input.copy_response)
    def _(): 
        text = AI_content()
        clipboard.copy(text)

app = App(app_ui, server)