import numpy as np
import pandas as pd
from cowidev.utils.clean import clean_date_series

from cowidev.testing import CountryTestBase


class Bolivia(CountryTestBase):
    location = "Bolivia"
    units = "tests performed"
    source_label = "Bolivia Ministry of Health"
    source_url = "https://raw.githubusercontent.com/dquintani/covid/main/pruebas_acum.csv"
    source_url_ref = "https://www.boligrafica.com/"
    notes = "Made available by BoliGráfica on GitHub"
    rename_columns = {"Unnamed: 0": "Date", "Bolivia": "Cumulative total"}

    # add hardcoded data prior to March 8 2020
    # def pipe_add_datapoint(self, df: pd.DataFrame) -> pd.DataFrame:
    #     hardcoded_data = pd.DataFrame(
    #         np.array(
    #             [
    #                 ["26", "2020-03-14", "https://minsalud.gob.bo/3977-corona-informe6"],
    #                 [
    #                     "33",
    #                     "2020-03-15",
    #                     "https://minsalud.gob.bo/3978-bolivia-registra-un-nuevo-caso-importado-de-coronavirus-y-22-descartados",
    #                 ],
    #                 [
    #                     "45",
    #                     "2020-03-16",
    #                     "https://minsalud.gob.bo/3980-ministro-de-salud-ratifica-que-no-hay-muertes-por-coronavirus-en-el-pais-y-descarta-34-casos-sospechosos",
    #                 ],
    #                 [
    #                     "50",
    #                     "2020-03-17",
    #                     "https://minsalud.gob.bo/3986-ministro-de-salud-reporta-un-nuevo-paciente-con-coronavirus-en-el-pais-y-sube-a-12-los-casos-confirmados",
    #                 ],
    #                 [
    #                     "51",
    #                     "2020-03-18",
    #                     "https://minsalud.gob.bo/3987-ministerio-de-salud-mantiene-en-12-el-numero-de-casos-confirmados-de-coronavirus",
    #                 ],
    #                 [
    #                     "84",
    #                     "2020-03-19",
    #                     "https://minsalud.gob.bo/3989-ministerio-de-salud-reporta-15-casos-confirmados-de-coronavirus-en-el-pais",
    #                 ],
    #                 [
    #                     "111",
    #                     "2020-03-20",
    #                     "https://minsalud.gob.bo/3992-ministro-de-salud-pide-extremar-las-medidas-de-prevencion-ante-aumento-de-casos-de-covid-19",
    #                 ],
    #                 [
    #                     "228",
    #                     "2020-03-22",
    #                     "https://minsalud.gob.bo/3999-ministro-de-salud-reporta-3-nuevos-casos-de-coronavirus-y-pide-extremar-las-medidas-de-distanciamiento-social",
    #                 ],
    #                 [
    #                     "273",
    #                     "2020-03-23",
    #                     "https://minsalud.gob.bo/4001-salud-reporta-un-nuevo-caso-de-coronavirus-y-sube-a-28-el-numero-de-personas-contagiadas-en-el-pais",
    #                 ],
    #                 [
    #                     "442",
    #                     "2020-03-26",
    #                     "https://minsalud.gob.bo/4008-casos-positivos-de-coronavirus-suben-a-61-en-bolivia-y-tres-contagiados-estan-en-terapia-intensiva",
    #                 ],
    #                 [
    #                     "697",
    #                     "2020-03-30",
    #                     "https://minsalud.gob.bo/4017-suben-a-107-los-casos-de-covid-19-en-el-pais-seis-pacientes-perecen-a-consecuencia-del-virus",
    #                 ],
    #                 [
    #                     "779",
    #                     "2020-03-31",
    #                     "https://minsalud.gob.bo/4020-gobierno-reporta-115-casos-positivos-de-covid-19-y-autoriza-a-laboratorios-publicos-y-privados-realizar-pruebas-de-diagnostico",
    #                 ],
    #                 [
    #                     "836",
    #                     "2020-04-01",
    #                     "https://minsalud.gob.bo/4021-salud-registra-un-nuevo-fallecido-por-coronavirus-cinco-personas-muestran-signos-de-recuperacion",
    #                 ],
    #                 [
    #                     "1118",
    #                     "2020-04-03",
    #                     "https://minsalud.gob.bo/4028-139-casos-de-covid-19-en-bolivia-y-gobierno-habilita-500-unidades-de-terapia-intensiva",
    #                 ],
    #                 [
    #                     "1549",
    #                     "2020-04-06",
    #                     "https://minsalud.gob.bo/4033-bolivia-acumula-194-casos-de-coronavirus-ministro-de-salud-pide-a-jovenes-y-adultos-cuidar-su-salud-ante-la-pandemia",
    #                 ],
    #                 [
    #                     "1681",
    #                     "2020-04-07",
    #                     "https://minsalud.gob.bo/4036-210-casos-de-covid-19-en-el-pais-ministro-cruz-pide-reflexion-y-recogimiento",
    #                 ],
    #                 [
    #                     "1875",
    #                     "2020-04-08",
    #                     "https://minsalud.gob.bo/4039-gobierno-reporta-54-nuevos-casos-de-coronavirus-en-el-pais",
    #                 ],
    #                 [
    #                     "1997",
    #                     "2020-04-09",
    #                     "https://minsalud.gob.bo/4040-ministerio-de-salud-reporta-268-casos-de-coronavirus-en-el-pais",
    #                 ],
    #                 [
    #                     "2185",
    #                     "2020-04-10",
    #                     "https://minsalud.gob.bo/4041-bolivia-acumula-275-casos-confirmados-de-coronavirus-y-20-fallecidos-en-un-mes",
    #                 ],
    #                 [
    #                     "2356",
    #                     "2020-04-11",
    #                     "https://minsalud.gob.bo/4042-el-pais-suma-300-casos-de-coronavirus-y-casi-la-mitad-estan-en-santa-cruz",
    #                 ],
    #                 [
    #                     "2528",
    #                     "2020-04-12",
    #                     "https://minsalud.gob.bo/4043-sube-a-27-las-muertes-y-a-330-los-casos-confirmados-de-covid-19-en-bolivia",
    #                 ],
    #                 [
    #                     "2919",
    #                     "2020-04-14",
    #                     "https://minsalud.gob.bo/4049-en-bolivia-se-reportan-397-casos-de-coronavirus-la-mayoria-son-mujeres",
    #                 ],
    #                 [
    #                     "3230",
    #                     "2020-04-15",
    #                     "https://minsalud.gob.bo/4055-bolivia-registra-44-nuevos-casos-de-covid-19-y-hay-169-sospechosos",
    #                 ],
    #                 [
    #                     "3419",
    #                     "2020-04-16",
    #                     "https://minsalud.gob.bo/4062-ministerio-de-salud-reporta-24-nuevos-casos-de-coronavirus-y-ya-son-26-los-pacientes-recuperados",
    #                 ],
    #                 [
    #                     "3573",
    #                     "2020-04-17",
    #                     "https://minsalud.gob.bo/4066-casos-de-coronavirus-suben-a-493-en-el-pais-y-31-pacientes-estan-en-recuperacion",
    #                 ],
    #                 [
    #                     "3923",
    #                     "2020-04-18",
    #                     "https://minsalud.gob.bo/4070-bolivia-reporta-520-casos-de-covid-19-y-gobierno-afirma-que-la-tendencia-de-contagios-es-menor",
    #                 ],
    #                 [
    #                     "4135",
    #                     "2020-04-19",
    #                     "https://minsalud.gob.bo/4074-bolivia-registra-44-nuevos-casos-y-acumula-564-casos-confirmados-de-covid-19",
    #                 ],
    #                 [
    #                     "4298",
    #                     "2020-04-20",
    #                     "https://minsalud.gob.bo/4078-gobierno-reporta-dos-primeros-casos-de-covid-19-en-beni-y-el-pais-suma-598-contagiados",
    #                 ],
    #                 [
    #                     "4420",
    #                     "2020-04-21",
    #                     "https://minsalud.gob.bo/4081-ministerio-de-salud-reporta-11-nuevos-casos-de-covid-19-y-44-pacientes-recuperados",
    #                 ],
    #                 [
    #                     "4855",
    #                     "2020-04-22",
    #                     "https://minsalud.gob.bo/4088-el-pais-registra-63-nuevos-casos-de-coronavirus-y-tres-decesos-en-un-dia",
    #                 ],
    #                 [
    #                     "4995",
    #                     "2020-04-23",
    #                     "https://minsalud.gob.bo/4093-bolivia-supera-los-700-casos-confirmados-de-covid-19-y-registra-43-fallecidos",
    #                 ],
    #                 [
    #                     "5297",
    #                     "2020-04-24",
    #                     "https://minsalud.gob.bo/4098-sube-a-807-el-numero-de-casos-de-coronavirus-en-el-pais-santa-cruz-es-la-region-mas-afectada",
    #                 ],
    #                 [
    #                     "5572",
    #                     "2020-04-25",
    #                     "https://minsalud.gob.bo/4099-ministerio-de-salud-reporta-866-casos-de-coronavirus-y-74-pacientes-recuperados",
    #                 ],
    #                 [
    #                     "5791",
    #                     "2020-04-26",
    #                     "https://minsalud.gob.bo/4102-bolivia-registra-84-nuevos-casos-de-coronavirus-y-acumula-un-total-de-950",
    #                 ],
    #                 [
    #                     "5988",
    #                     "2020-04-27",
    #                     "https://minsalud.gob.bo/4103-bolivia-supera-los-1-000-casos-de-coronavirus-y-reporta-98-pacientes-recuperados",
    #                 ],
    #                 [
    #                     "6121",
    #                     "2020-04-28",
    #                     "https://minsalud.gob.bo/4106-ministerio-de-salud-registra-39-nuevos-casos-de-coronavirus-y-suma-110-pacientes-recuperados-en-el-pais",
    #                 ],
    #                 [
    #                     "6551",
    #                     "2020-04-30",
    #                     "https://minsalud.gob.bo/4116-pacientes-con-coronavirus-llegan-a-1-167-en-el-pais-y-132-se-recuperan",
    #                 ],
    #                 ["6975", "2020-05-01", "https://minsalud.gob.bo/4120-reporte-covid-0501"],
    #                 [
    #                     "7651",
    #                     "2020-05-02",
    #                     "https://minsalud.gob.bo/4123-bolivia-registra-241-personas-infectadas-con-mayor-porcentaje-en-santa-cruz-y-beni",
    #                 ],
    #                 [
    #                     "8080",
    #                     "2020-05-03",
    #                     "https://minsalud.gob.bo/4126-bolivia-confirma-124-personas-con-coronavirus-y-suma-en-total-1-594-contagiados",
    #                 ],
    #                 [
    #                     "8611",
    #                     "2020-05-04",
    #                     "https://minsalud.gob.bo/4129-se-elevan-a-1-681-las-personas-contagiadas-con-coronavirus-y-hay-174-recuperadas",
    #                 ],
    #                 [
    #                     "8995",
    #                     "2020-05-05",
    #                     "https://minsalud.gob.bo/4132-bolivia-suma-121-personas-contagiadas-de-coronavirus-y-supera-las-1-800-a-nivel-nacional",
    #                 ],
    #                 [
    #                     "9156",
    #                     "2020-05-06",
    #                     "https://minsalud.gob.bo/4135-reportan-84-nuevos-contagios-y-sube-a-1-886-las-personas-infectadas-por-covid-19",
    #                 ],
    #                 [
    #                     "10099",
    #                     "2020-05-07",
    #                     "https://minsalud.gob.bo/4137-bolivia-supera-los-2-000-contagios-de-covid-19",
    #                 ],
    #             ]
    #         ),
    #         columns=["Cumulative total", "Date", "Source URL"],
    #     )
    #     hardcoded_data["Country"] = "Bolivia"
    #     hardcoded_data["Units"] = "tests performed"
    #     hardcoded_data["Source label"] = "Ministry of Health"
    #     hardcoded_data["Notes"] = ""

    #     return df.append(hardcoded_data, ignore_index=True)

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url, usecols=["Unnamed: 0", "Bolivia"]).dropna()
        df["Bolivia"] = df["Bolivia"].astype(int)
        df["Unnamed: 0"] = clean_date_series(df["Unnamed: 0"])

        return df

    def pipe_filter_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.drop_duplicates(subset="Cumulative total").drop_duplicates(subset="Date")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_filter_rows)
            .pipe(self.pipe_metadata)
            #            .pipe(self.pipe_add_datapoint)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Bolivia().export()
