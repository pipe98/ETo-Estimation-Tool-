import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from  tkcalendar import DateEntry
import math

# ------------------------------------------------------
# Función para procesar datos al hacer clic en "Aceptar"
# ------------------------------------------------------

def procesar_datos():
    fecha_str = entry_fecha.get()
    zona = combo_zona.get()
    c = 0.16 if zona == "Interior" else 0.19
    try:
        altitud = float(entry_altitud.get())
    except ValueError:
        print("Error: Altitud no válida.")
        ventana.quit()
        return
    
    unidad_tmax = combo_tmax.get()
    unidad_tmin = combo_tmin.get()
    unidad_tdew = combo_tdew.get()
    unidad_viento = combo_viento.get()

    try:
        latitud = float(entry_latitud.get())
    except ValueError:
        print("Latitud inválida.")
        return
    phi = math.radians(latitud)

    # Cerrar ventana
    ventana.destroy()

    # Selección de archivo
    archivo = filedialog.askopenfilename(title="Selecciona el archivo .xlsx", filetypes=[("Excel files","*.xlsx")])

    if not archivo:
        print("No se seleccionó ningún archivo.")
        return
    
    # Leer archivo
    df = pd.read_excel(archivo, header=None)
    df.columns =["Tmax", "Tmin", "Tdew", "viento"]

    # Conversión de unidades
    if unidad_tmax == "°F":
        df["Tmax"] = (df["Tmax"]-32)*(5/9)
    
    if unidad_tmin == "°F":
        df["Tmin"] = (df["Tmin"]-32)*(5/9)

    if unidad_tdew == "°F":
        df["Tdew"] = (df["Tdew"]-32)*(5/9)

    if unidad_viento == "nudos":
        df["viento"] = df["viento"]*0.514444

    # Cálculo de presión y gamma
    P = 101.3*((293-0.0065*altitud)/293)**5.26 # Presión (kPa)
    gamma = 0.000665*P # Constante psicrométrica (kPa/°C)

    # Cálculo de presión de vapor de saturación (es, kPa)
    es_max =0.6108*np.exp((17.27*df["Tmax"])/(df["Tmax"]+237.3))
    es_min =0.6108*np.exp((17.27*df["Tmin"])/(df["Tmin"]+237.3))
    df["es"] = (es_max + es_min)/2

    # Cálculo de la presión real de vapor (ea, kPa)
    df["ea"] = 0.6108*np.exp((17.27*df["Tdew"])/(df["Tdew"]+237.3))

    # Cálculo del déficit de presión de vapor (DPV, kPa)
    df["DPV (kPa)"] = df["es"] - df["ea"]

    # Calcular temperatura media
    Tmed = (df["Tmax"] + df["Tmin"])/2

    # Calcular pendiente de la curva de presión de saturación (Delta)
    df["Delta (kPa/°C)"] = (4098*df["es"])/((Tmed+237.3)**2)

    # Convertir fecha y calcular días julianos
    # ----Convertir fecha inicial
    try:
        fecha_inicio = datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        print("Fecha inválida. Usa el formato dd/mm/aaaa")
        return
    # ----Calcular días julianos para cada fila
    dias_julianos = []
    for i in range(len(df)):
        fecha = fecha_inicio + timedelta(days=i)
        dia_juliano = fecha.timetuple().tm_yday
        dias_julianos.append(dia_juliano)

    df.insert(0,"Día juliano", dias_julianos)  
    
    # Cálculo de dr, delta y ws
    dias_julianos = df["Día juliano"]
    # ---Distancia relativa Tierra-sol
    df["dr"] = 1 + 0.033*np.cos(2*np.pi*dias_julianos/365)
    # ---Declinación solar (en radianes)
    df["d (rad)"] = 0.409*np.sin((2*np.pi*dias_julianos/365)-1.39)
    # ---Ángulo horario al atardecer (en radianes)
    df["ws (rad)"] = np.arccos(-np.tan(phi)*np.tan(df["d (rad)"]))

    # Cálculo de radiación
    # ---Constantes
    Gsc = 0.0820 # constante solar MJ/m2/min
    albedo = 0.23
    # ---Ra: radiación extraterrestre---
    Ra = (24*60/np.pi)*Gsc*df["dr"]*((np.sin(phi)*np.sin(df["d (rad)"]))+(np.cos(phi)*np.cos(df["d (rad)"])*np.sin(df["ws (rad)"])))
    df["Ra (MJ/m2/d)"] = Ra
    # ---Rs: radiación solar estimada---
    Rs = c*((df["Tmax"]-df["Tmin"])**0.5)*Ra
    df["Rs (MJ/m2/d)"] = Rs
    # ---Rns: radiación neta de onda corta---
    Rns = (1-albedo)*df["Rs (MJ/m2/d)"]
    df["Rns (MJ/m2/d)"] = Rns
    # ---Rso: radiación solar despejada---
    Rso = (0.75+(2e-5*altitud))*Ra
    df["Rso (MJ/m2/d)"] = Rso
    # ---Rnl: radiación neta de onda larga---
    sigma = 4.903e-9 # Cte. de Stefan-Boltzmann MJ/K4/m2/d
    Tmax_K = df["Tmax"]+273.16
    Tmin_K = df["Tmin"]+273.16
    Rnl = sigma*((Tmax_K**4 + Tmin_K**4)/2)*(0.34-0.14*np.sqrt(df["ea"]))*(1.35*(df["Rs (MJ/m2/d)"]/df["Rso (MJ/m2/d)"])-0.35)
    df["Rnl (MJ/m2/d)"] = Rnl
    # ---Rn: radiación neta total---
    Rn = df["Rns (MJ/m2/d)"]-df["Rnl (MJ/m2/d)"]
    df["Rn (MJ/m2/d)"] = Rn

    # Cálculo de ETo Manual de la FAO No.56
    # ---Temperatura media---
    Tmed = (df["Tmax"]+df["Tmin"])/2
    # ---Flujo de calor al suelo (G=0)
    G = 0
    # ---Velocidad del viento a 2 m
    u2 = df["viento"]
    # ---ETo
    ETo = ((0.408*df["Delta (kPa/°C)"]*(df["Rn (MJ/m2/d)"]-G))+(gamma*(900/(Tmed+273))*u2*df["DPV (kPa)"]))/(df["Delta (kPa/°C)"]+gamma*(1+0.34*u2))
    df["ETo (mm/d)"] = ETo

    # Redondear cifras decimales
    df = df.round(3)

    # Renombrar columnas
    df.rename(columns={
        "Tmax": "Tmax (°C)",
        "Tmin": "Tmin (°C)",
        "Tdew": "Trocío (°C)",
        "viento": "Vviento (m/s)"
    }, inplace=True)

    # Seleccionar los resultados de exportación
    df = df[["Tmax (°C)", "Tmin (°C)", "Trocío (°C)", "Vviento (m/s)", "DPV (kPa)", "Delta (kPa/°C)","dr", "d (rad)", "ws (rad)"
             , "Ra (MJ/m2/d)", "Rs (MJ/m2/d)", "Rns (MJ/m2/d)", "Rso (MJ/m2/d)", "Rnl (MJ/m2/d)", "Rn (MJ/m2/d)", "ETo (mm/d)" ]]              

    print(f"\n Primeras 5 filas del archivo convertido:")
    print(df.head())
    print(f"\n Altitud: {altitud} msnm")
    print(f"Constante psicrométrica (gamma): {gamma:.3f} kPa/°C")
    
    # elegir ubiación y nombre del archivo de salida
    
    ruta_guardado = filedialog.asksaveasfilename(
        defaultextension = ".xlsx",
        filetypes = [("Excel files",".xlsx")],
        title="Guardar archivo como"
        )

    if ruta_guardado:
        df.to_excel(ruta_guardado, index=False)
        print(f"\n Archivo guardado exitosamente en:\n{ruta_guardado}")
    else:
        print("No se guardó el archivo.")

# ---------------------------------
# Crear ventana
# ---------------------------------
ventana = tk.Tk()
ventana.title("ETo:")

# Widgets
tk.Label(ventana, text="Altitud (msnm):").grid(row=0, column=0, sticky="w")
entry_altitud =tk.Entry(ventana)
entry_altitud.grid(row=0,column=1)

tk.Label(ventana, text="Unidad Tmax:").grid(row=1, column=0, sticky="w")
combo_tmax = ttk.Combobox(ventana, values=["°C", "°F"])
combo_tmax.grid(row=1, column=1)
combo_tmax.set("°C")

tk.Label(ventana, text="Unidad Tmin:").grid(row=2, column=0, sticky="w")
combo_tmin = ttk.Combobox(ventana, values=["°C", "°F"])
combo_tmin.grid(row=2, column=1)
combo_tmin.set("°C")

tk.Label(ventana, text="Unidad Trocío:").grid(row=3, column=0, sticky="w")
combo_tdew = ttk.Combobox(ventana, values=["°C", "°F"])
combo_tdew.grid(row=3, column=1)
combo_tdew.set("°C")

tk.Label(ventana, text="Unidad viento:").grid(row=4, column=0, sticky="w")
combo_viento = ttk.Combobox(ventana, values=["m/s", "nudos"])
combo_viento.grid(row=4, column=1)
combo_viento.set("m/s")

tk.Label(ventana, text="Fecha inicial:").grid(row=5, column=0, sticky="w")
entry_fecha = DateEntry(ventana, date_pattern='dd/mm/yyyy', locale='es_MX')
entry_fecha.grid(row=5, column=1)

tk.Label(ventana, text="Latitud (°decimales):").grid(row=6, column=0, sticky="w")
entry_latitud = tk.Entry(ventana)
entry_latitud.grid(row=6, column=1)

tk.Label(ventana, text="Zona geográfica:").grid(row=7, column=0, sticky="w")
combo_zona = ttk.Combobox(ventana, values=["Interior", "Costa"])
combo_zona.grid(row=7, column=1)
combo_zona.set("Interior") # valor por defecto

# Botón aceptar
boton_aceptar = tk.Button(ventana, text="Aceptar", command=procesar_datos)
boton_aceptar.grid(row=8, column=0, columnspan=2, pady=10)

ventana.mainloop()