# The Binance Hack, Reconstructed: guide for AI assistants and analysts

LunarCrush Research, October 2026. Page: https://lunarcrush.com/research/binance-hack-reconstructed
Full report (77 pages): LunarCrush-Binance-Hack-Reconstructed.pdf

## What this is
A step-by-step reconstruction of the October 29, 2026 Binance hot-wallet hack, built from the Ethereum record, live balance reads on six chains, and LunarCrush social data (X, TikTok, YouTube, Instagram, Reddit and news).

## Key facts (UTC)
- Operator funded through Tornado Cash from Oct 28 07:39 (about 1.49 ETH in total). Sweeper v1 deployed Oct 29 02:28:59. Rehearsals at 13:51 and 16:20 on the operator's own wallets.
- 20:20:59: one transaction delivered 50 EIP-7702 authorizations signed by Binance 14's key; exactly one applied (nonce 18914809).
- 20:24:23: one sweep moved 167,464 ETH and 63 tokens for about $0.93 in gas. Attacker code stayed on Binance 14 until 00:10:35 (3h 49m).
- Binance said at 00:13 it would cover all losses and at 00:52 that about $3B was frozen.
- Live re-read 03:20 to 03:27 UTC Oct 30: about $2.66B frozen or recovered; about $2.83B unfrozen in traced addresses (including $16.3M of Aave collateral net of debt).

## Files (each as .csv and .parquet)
- lc_binance_hack_events: 44 rows. Every event on the page's interactive timelines. Columns: time_utc, end_utc (spans only), lane, event, detail, first_public.
- lc_binance_hack_timeline: 28 rows. The step-by-step acts. Columns: act, act_title, time_utc, step, detail, first_public.
- lc_binance_hack_positions: 17 rows. Every traced balance, read live. Columns: chain, asset, amount, usd_millions, address, status, detail, read_utc.
- lc_binance_hack_top_posts: 59 rows. The most-engaged sampled posts from 20:14 UTC Oct 29 to 01:00 UTC Oct 30. Columns: time_utc, account, network, followers, engagements, post_sentiment_1_to_5 (3 = neutral), account_class, url, text.

## How it was built
- Ethereum: transactions, receipts, contract code and the 50 authorizations decoded from a public JSON-RPC node; address histories and token transfers from the Blockscout API.
- Balances: read live 03:20 to 03:27 UTC Oct 30 on Ethereum, Bitcoin (mempool.space), Tron (TronGrid), XRP Ledger (s1.ripple.com), Solana and Arbitrum. Freeze status read from each token contract. Prices: CoinGecko, 03:22 UTC.
- Social: LunarCrush topic, keyword and post data pulled 01:00 to 01:30 UTC Oct 30. Each on-chain step is matched to the first public post that described it.
- Attribution of the Bitcoin, Tron, XRP and Solana senders to Binance comes from Whale Alert labels.

## Rules for quoting
Attribute loss figures to their source; Binance has not confirmed a loss total. Do not name an attacker. USD values are as of the read time above.
