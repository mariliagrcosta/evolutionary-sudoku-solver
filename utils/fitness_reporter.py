import pandas as pd
import os

def generate_fitness_reports(all_run_data, output_folder_path):
    if not all_run_data:
        print("Nenhum dado de execução encontrado para gerar relatórios de aptidão (max/min/avg).")
        return

    try:
        os.makedirs(output_folder_path, exist_ok=True)
        print(f"\nGerando relatórios de evolução da aptidão (max/min/avg) na pasta: {output_folder_path}")
    except Exception as e:
        print(f"ERRO: Não foi possível criar o diretório de saída '{output_folder_path}' para relatórios max/min/avg: {e}")
        return

    reports_generated_count = 0
    for run_data in all_run_data:
        file_name = run_data.get("Arquivo", "N/A")
        exec_type = run_data.get("Tipo_Execucao", "N/A")
        history = run_data.get("fitness_history", [])

        if not history:
            continue

        try:
            fitness_df = pd.DataFrame(history)
            for col in ['Maior_Aptidao', 'Menor_Aptidao', 'Media_Aptidao']:
                if col in fitness_df.columns:
                    fitness_df[col] = fitness_df[col].apply(lambda x: f"{x:.6f}")

            base_name = os.path.splitext(file_name)[0]
            report_filename = f"{base_name}_{exec_type}_fitness_summary.xlsx"
            full_output_path = os.path.join(output_folder_path, report_filename)

            if 'Geracao' in fitness_df.columns:
                 fitness_df = fitness_df[['Geracao', 'Maior_Aptidao', 'Menor_Aptidao', 'Media_Aptidao']]
            else: 
                 fitness_df = fitness_df[['Maior_Aptidao', 'Menor_Aptidao', 'Media_Aptidao']]


            fitness_df.to_excel(full_output_path, index=False, sheet_name="Evolucao_Aptidao_Resumo")
            reports_generated_count += 1

        except ImportError:
            print("\nERRO: Para gerar o relatório de aptidão (max/min/avg), as bibliotecas pandas e openpyxl são necessárias.")
            print("Por favor, instale-as com: pip install pandas openpyxl")
            return
        except Exception as e:
            print(f"\nOcorreu um erro inesperado ao tentar salvar o relatório max/min/avg para '{file_name}' ({exec_type}): {e}")

    if reports_generated_count > 0:
        print(f"{reports_generated_count} relatórios de aptidão (max/min/avg) individuais foram salvos com sucesso.")
    else:
        print("Nenhum histórico de aptidão do AG (max/min/avg) foi encontrado para gerar relatórios.")

def generate_boxplot_data_reports(all_run_data, output_folder_path):
    if not all_run_data:
        print("Nenhum dado de execução encontrado para gerar relatórios para boxplot.")
        return

    try:
        os.makedirs(output_folder_path, exist_ok=True)
        print(f"\nGerando relatórios de dados para boxplot na pasta: {output_folder_path}")
    except Exception as e:
        print(f"ERRO: Não foi possível criar o diretório de saída '{output_folder_path}' para relatórios de boxplot: {e}")
        return

    reports_generated_count = 0
    for run_data in all_run_data:
        file_name = run_data.get("Arquivo", "N/A")
        exec_type = run_data.get("Tipo_Execucao", "N/A")
        boxplot_data_list = run_data.get("boxplot_data", [])

        if not boxplot_data_list:
            continue

        try:
            transformed_data_for_df = []
            for generation_data in boxplot_data_list:
                gen_num = generation_data['Geracao']
                for fitness_score in generation_data['Todas_Aptidoes']:
                    transformed_data_for_df.append({
                        'Geracao': gen_num,
                        'Aptidao_Individuo': fitness_score
                    })

            if not transformed_data_for_df:
                continue

            boxplot_df = pd.DataFrame(transformed_data_for_df)

            if 'Aptidao_Individuo' in boxplot_df.columns:
                boxplot_df['Aptidao_Individuo'] = boxplot_df['Aptidao_Individuo'].apply(lambda x: f"{x:.6f}")

            base_name = os.path.splitext(file_name)[0]
            report_filename = f"{base_name}_{exec_type}_boxplot_data.xlsx"
            full_output_path = os.path.join(output_folder_path, report_filename)

            boxplot_df = boxplot_df[['Geracao', 'Aptidao_Individuo']]

            boxplot_df.to_excel(full_output_path, index=False, sheet_name="Dados_Aptidao_Boxplot")
            reports_generated_count += 1

        except ImportError:
            print("\nERRO: Para gerar o relatório de dados para boxplot, as bibliotecas pandas e openpyxl são necessárias.")
            print("Por favor, instale-as com: pip install pandas openpyxl")
            return
        except Exception as e:
            print(f"\nOcorreu um erro inesperado ao tentar salvar o relatório de dados para boxplot para '{file_name}' ({exec_type}): {e}")

    if reports_generated_count > 0:
        print(f"{reports_generated_count} relatórios de dados para boxplot individuais foram salvos com sucesso.")
    else:
        print("Nenhum dado de aptidão do AG foi encontrado para gerar relatórios para boxplot.")