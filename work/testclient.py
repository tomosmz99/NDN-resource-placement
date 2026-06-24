# testclient.py
import asyncio
from ndn.app import NDNApp

async def main():
    app = NDNApp()
    # 1. Managerに対して子コンテナ作成のInterestを送信
    target_interest = '/manager/create/producer_1/test-child-container/512/256m'
    print(f" [Client] Managerにリクエスト送信: {target_interest}")
    
    try:
        _, _, content = await app.express_interest(target_interest, must_be_fresh=True)
        response = bytes(content).decode('utf-8')
        print(f" [Client] Managerからの応答: {response}")
        
        # 2. 返り値が「Redirect:」で始まっていれば、その宛先へ再送
        if response.startswith("Redirect:"):
            spy_prefix = response.split("Redirect:")[1]
            print(f" [Client] Spyへリダイレクト送信: {spy_prefix}")
            
            _, _, spy_content = await app.express_interest(spy_prefix, must_be_fresh=True)
            print(f"🎉 [Client] Spyからの最終応答: {bytes(spy_content).decode('utf-8')}")
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    finally:
        app.shutdown()

if __name__ == '__main__':
    asyncio.run(main())