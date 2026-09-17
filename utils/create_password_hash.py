"""
Tien ich tao chuoi mat khau ma hoa bang bcrypt cho Cong thong tin Metalic.
Chay doc lap bang lenh:
    python utils/create_password_hash.py
"""
import getpass
import bcrypt

def generate_hash(plain_password: str) -> str:
    """
    Ma hoa mat khau plain text sang chuoi bcrypt hash.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def main():
    print("=" * 60)
    print("  METALIC VIET NAM - CONG CU TAO MAT KHAU MA HOA BCRYPT")
    print("=" * 60)
    
    pwd = getpass.getpass("Nhap mat khau can ma hoa (an ky tu khi go): ")
    if not pwd:
        print("[Loi] Mat khau khong duoc de trong!")
        return
        
    confirm_pwd = getpass.getpass("Xac nhan lai mat khau: ")
    if pwd != confirm_pwd:
        print("[Loi] Mat khau xac nhan khong khop!")
        return
        
    hashed_value = generate_hash(pwd)
    print("\n--> MA HOA THANH CONG!")
    print("Gia tri Password_Hash de copy vao Google Sheets (cot Password_Hash):")
    print("-" * 60)
    print(hashed_value)
    print("-" * 60)
    print("Luu y: Tuyet doi khong luu mat khau goc o dang van ban thuan.")

if __name__ == "__main__":
    main()
