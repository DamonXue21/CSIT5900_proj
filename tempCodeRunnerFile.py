放 system prompt（每次都放最新版本）
            messages.append({"role": "system", "content": SYSTEM_PROMPT})

            # 加入之前的歷史對話
            for prev_user, prev_ai in self.history:
                messages.append({"role": "user", "content": prev_user})
                messages.append({"role": "assistant", "content": prev_ai})

            # 加入這次的用戶輸入
            messages.append({"ro