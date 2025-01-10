import hashlib

def generate_key(hardware_id):
    """
    Gera a chave de ativação com base no Hardware ID.
    """
    secret_suffix = "X9A3Z7B6Q2T5L8C1"  # Sufixo secreto usado para gerar a chave
    raw_key = hardware_id + secret_suffix
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return hashed_key

def main():
    print("==== Validador de Chave - NeuroEQ ====")
    hardware_id = input("Digite o Hardware ID recebido do cliente: ").strip()
    if not hardware_id:
        print("Erro: Hardware ID não pode estar vazio.")
        return

    # Gera a chave correspondente ao Hardware ID
    activation_key = generate_key(hardware_id)

    print("\n=== Chave Gerada ===")
    print(f"Hardware ID: {hardware_id}")
    print(f"Chave de Ativação: {activation_key}")
    print("====================")
    print("\nForneça esta chave ao cliente para ativar o sistema.")

if __name__ == "__main__":
    main()
