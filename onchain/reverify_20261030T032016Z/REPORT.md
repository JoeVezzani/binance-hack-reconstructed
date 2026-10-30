# Flow chapter re-verification, live on-chain reads
Real read window: 2026-10-30 03:20:16 to 03:26:49 UTC (date -u at start 03:17:13 UTC). Prices: CoinGecko 03:22:05 UTC (BTC 77,253; ETH 2,209.99; XRP 1.23; SOL 95.55; XAUt 3,986.22; wBETH 2,447; ARB 0.1558). Stablecoins at face. ETH head block 26,302,839; BTC tip 973,766. Every raw response is saved here with its own utc field; _read_log.json lists all requests.

Original problem: flow.json / synthesis.json / flow_summary.json claimed reads at "03:30 to 04:30" / "04:30 UTC", times that had not yet occurred. The underlying pulls (onchain/flow*.json) were taken about 02:56 to 03:06 UTC and are processed outputs, not raw responses.

| Claim | Live value (UTC read) | Source | Verdict |
|---|---|---|---|
| 0x5227 1,175,464,713 USDT blacklisted | 1,175,464,712.78, isBlackListed=true (03:20:17) | publicnode | CONFIRMED |
| 0x5227 823M USDC blacklisted | 823,000,000, isBlacklisted=true (03:20:17) | publicnode | CONFIRMED |
| 0xAa246BF6 174,999,872 USDT blacklisted | same, true (03:20:20) | publicnode | CONFIRMED |
| Tron TG5iBMQP 312.7M USDT "frozen 21:10" | 312,729,468, isBlackListed=true (03:22:28) | TronGrid | CONFIRMED; 21:10 UNSUPPORTED, dropped |
| Tron 75M swapped, ~$225M unaccounted | TG5i got 612,729,468 at 20:22:45; sent 300M to TPBkSjkC (20:45:51, 20:56:09); TPBk sent 300M in 18 transfers 20:46 to 21:16: 199M contract TSUUVjys, 33M contract PoolManager TVjuTE3V, 2M contract TFGDbUyP, 0.01M TXJgMdjV, 65.99M TCzBTkqn (still held, blacklisted); TPBk blacklisted, empty (03:24 to 03:25) | TronGrid | CHANGED: 378.7M frozen, ~234M to contracts |
| XAUt freeze not readable | 12,574.05 XAUt, isBlocked=true, controls false (03:20:28) | publicnode + Blockscout ABI | CHANGED: frozen $50.1M |
| USD1 27.8M per World Liberty | 27,824,039.94, frozen()=true, control false (03:26:49) | publicnode + Blockscout ABI | CHANGED: verified |
| Aave 60M aUSDT vs 19,763 WETH | 60,002,066.5 aUSDT; 19,762.70 debt; USDT reserve isFrozen=true (03:20:29) | publicnode, Aave data provider | CONFIRMED; counted net $16.2M |
| Arbitrum $30.5M recovered | 8,426 ETH + 74,559,805 ARB left 0x3E2bf1ac 00:18:20 via type 0x65 L1-originated txs; now 0.48 ETH, 0 ARB (03:20:35) | Arbitrum publicnode/Blockscout | CONFIRMED moved; $30.2M; attribution @zachxbt |
| 0x8532fa14 197,460 ETH | 197,460.005, nonce 0 (03:20:17) | publicnode | CONFIRMED |
| 0xc887af69 137,602 ETH | 137,602.0015, nonce 0 (03:20:18) | publicnode | CONFIRMED |
| 57,892 ETH still hopping | 0xCcBEF956 to 0xb171cA86 21:16:47 to 0x897C80d1 21:35:59; 0x897C 78,415.25 ETH nonce 0 (+20,523 from 0x42CDF00c) (03:24:13) | Blockscout, publicnode | CHANGED |
| 0x5227 15,139 ETH | 16,501.5 ETH, last swap 03:17:23 | publicnode | CHANGED |
| ~408,000 ETH ($902M) | 429,979 ETH ($950.3M) | | CHANGED |
| 14,270 BTC in 15 parcels + ~4,000 unresolved | All 18,270.2 BTC in 19 addresses (17x1,000, 832.5, 437.7), no outputs spent; tree depth 4, 30 nodes (03:20:38 to 03:21:20) | mempool.space | CHANGED |
| ~1,580 BTC from unattributed address | All 15 funding txs from bc1qm34lsc65 (16,689.8 + 1,580.4) | mempool.space | CHANGED |
| XRP rK21 233.5M, no outgoing | 233,461,943.10, Flags 0, 0 txs sent (03:21:56) | s1.ripple.com | CONFIRMED |
| XRP 20:05, senders ~10 XRP | tx 78E31E7B 20:05:00 tesSUCCESS; senders 9.997 to 12.99 XRP | s1.ripple.com | CONFIRMED |
| SOL AffzFDKZ 970,545 | 970,545.253; oldest sig = 20:10:18 transfer (03:22:00) | Solana RPC | CONFIRMED |
| Blacklisted stablecoins $2.49B | $2,580.0M face | | CHANGED |
| 81% of $3.06B caught | not derivable | | UNSUPPORTED, dropped |
| Solana 303M USDT 23:03 | not re-read | | UNSUPPORTED, dropped |
| Delegation 20:20:59 / sweep 20:24:23 | from forensics raw, not re-read | | kept, out of scope |

Source failures: tronscanapi accountv2 HTTP 401 (key now required); TronGrid used instead. All other sources OK.

Totals: Frozen or recovered $2,676.5M (contract-verified frozen $2,630.1M + Arbitrum $30.2M + Aave net $16.2M). Unfrozen traced $2,814.8M (BTC 1,411.4; ETH 950.3; XRP 287.2; SOL 92.7; wBETH 73.2). Gross $5,491.3M. Original: 2.60B / 2.82B / 5.42B.
