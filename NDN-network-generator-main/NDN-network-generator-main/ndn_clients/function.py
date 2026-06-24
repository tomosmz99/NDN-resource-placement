from lib.ndn_function import NDNFunction
import sys

# ここが function の中身
def function_request_handler(name: str, args: list[bytes]) -> bytes:
    args = [arg.decode() for arg in args]
    args = ",".join(args)
    return f"Hello, {name}! Args: {args}".encode()

# function ノードが producer リクエストを捌く場合
def data_request_handler(name: str) -> str:
    print(f"Interest: {name}")
    return "DATA"


if __name__ == '__main__':
    producer = NDNFunction()
    # ここで引数からprefixを取得する
    if len(sys.argv) < 2:
        print("Usage: python function.py <prefix>")
        sys.exit(1)
    prefix = sys.argv[1]
    producer.run(prefix, function_request_handler, data_request_handler)
    