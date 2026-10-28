async def despachador_redes(video_path, titulo_yt, link):
    descripcion_yt = f"Descubre cómo funciona tu mente.\nEl libro recomendado (gratis el primer mes) aquí: {link}\n#psicologia #desarrollopersonal #shorts"
    titulo_tk = f"{titulo_yt} #psicologia #desarrollopersonal"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Flujo YouTube (Solo se ejecuta si existe YOUTUBE_STATE con contenido válido)
        if YOUTUBE_STATE and len(YOUTUBE_STATE.strip()) > 5:
            try:
                y_data = json.loads(YOUTUBE_STATE)
                # Si se pegó como una lista directa de cookies, la empaquetamos para Playwright
                if isinstance(y_data, list):
                    y_data = {"cookies": y_data, "origins": []}
                
                r_yt = "yt_state_tmp.json"
                with open(r_yt, "w", encoding="utf-8") as f:
                    json.dump(y_data, f)
                    
                ctx_yt = await browser.new_context(storage_state=r_yt, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                await subir_youtube(await ctx_yt.new_page(), video_path, titulo_yt, descripcion_yt)
                await ctx_yt.close()
            except Exception as e:
                print(f"⚠️ Omitiendo YouTube por error en el estado: {e}")
        else:
            print("ℹ️ YOUTUBE_STATE no configurado u omitido; saltando YouTube.")

        # 2. Flujo TikTok (Usa el JSON que acabamos de extraer)
        if TIKTOK_STATE and len(TIKTOK_STATE.strip()) > 5:
            try:
                t_data = json.loads(TIKTOK_STATE)
                if isinstance(t_data, list):
                    t_data = {"cookies": t_data, "origins": []}
                
                r_tk = "tk_state_tmp.json"
                with open(r_tk, "w", encoding="utf-8") as f:
                    json.dump(t_data, f)
                    
                ctx_tk = await browser.new_context(storage_state=r_tk, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                await subir_tiktok(await ctx_tk.new_page(), video_path, titulo_tk)
                await ctx_tk.close()
            except Exception as e:
                print(f"⚠️ Error procesando TIKTOK_STATE: {e}")
        else:
            print("⚠️ TIKTOK_STATE está vacío.")
            
        await browser.close()
