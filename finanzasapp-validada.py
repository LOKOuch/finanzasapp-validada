import streamlit as st
import sqlite3
import datetime

# --- Configuración de la base de datos ---
conn = sqlite3.connect('finanzasapp.db', check_same_thread=False)
c = conn.cursor()

# Crear tablas de usuarios y transacciones
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    balance REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    transaction_type TEXT,
    amount REAL,
    date TEXT,
    status TEXT)''')
conn.commit()

# --- Funciones mejoradas ---
def user_exists(username):
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    return c.fetchone() is not None

def register_user(username, password, initial_balance=1000):
    if not username or not password:
        st.error("Usuario y contraseña no pueden estar vacíos.")
        return
    if user_exists(username):
        st.error("El usuario ya existe.")
        return
    c.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
              (username, password, initial_balance))
    conn.commit()
    st.success("Usuario registrado correctamente.")

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def create_transaction(user_id, transaction_type, amount):
    if amount <= 0:
        st.error("El monto debe ser mayor que cero.")
        return
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = c.fetchone()[0]
    if transaction_type == "Retiro" and amount > balance:
        st.error("Saldo insuficiente para realizar esta transacción.")
        return
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_balance = balance - amount if transaction_type == "Retiro" else balance + amount
    c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    c.execute("INSERT INTO transactions (user_id, transaction_type, amount, date, status) VALUES (?, ?, ?, ?, ?)",
              (user_id, transaction_type, amount, date, "completada"))
    conn.commit()
    st.success(f"{transaction_type} de ${amount} realizada correctamente.")

def get_transactions(user_id):
    c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
    return c.fetchall()

# --- Interfaz Streamlit ---
st.title("FinanzasApp - Gestión Financiera")

menu = ["Inicio", "Registro", "Login", "Realizar Transacción", "Ver Transacciones", "Ver Balance"]
choice = st.sidebar.selectbox("Menú", menu)

if choice == "Registro":
    st.subheader("Registro de Usuario")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type='password')
    initial_balance = st.number_input("Saldo inicial", min_value=0.0, value=1000.0)
    if st.button("Registrar"):
        register_user(username, password, initial_balance)

elif choice == "Login":
    st.subheader("Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type='password')
    if st.button("Ingresar"):
        user = login_user(username, password)
        if user:
            st.session_state['user'] = user
            st.success(f"Bienvenido {user[1]}")
        else:
            st.error("Usuario o contraseña incorrectos.")

elif choice == "Realizar Transacción":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión.")
    else:
        st.subheader("Realizar Transacción")
        transaction_type = st.selectbox("Tipo de transacción", ["Depósito", "Retiro"])
        amount = st.number_input("Monto", min_value=0.01)
        if st.button("Realizar"):
            create_transaction(st.session_state['user'][0], transaction_type, amount)

elif choice == "Ver Transacciones":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión.")
    else:
        st.subheader("Listado de Transacciones")
        transactions = get_transactions(st.session_state['user'][0])
        for transaction in transactions:
            st.write(f"ID: {transaction[0]} | Tipo: {transaction[2]} | Monto: ${transaction[3]} | Fecha: {transaction[4]} | Estado: {transaction[5]}")

elif choice == "Ver Balance":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión.")
    else:
        st.subheader("Tu Balance")
        c.execute("SELECT balance FROM users WHERE id = ?", (st.session_state['user'][0],))
        balance = c.fetchone()[0]
        st.write(f"Tu balance actual es: ${balance:.2f}")

else:
    st.write("Selecciona una opción en el menú de la izquierda.")
