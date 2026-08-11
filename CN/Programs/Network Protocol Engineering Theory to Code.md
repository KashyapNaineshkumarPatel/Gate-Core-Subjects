# 🌐 Network Protocol Engineering: Theory to Code

A sequential collection of tools, simulators, and algorithms demonstrating the core mechanics of Computer Networks. 

This repository is designed as a **1:1 Mapping of Theory to Execution**. The folders are ordered chronologically to match a standard core engineering learning path. You do not just read about the protocols here; you build the mathematical engines that run them.

## 📖 How to Use This Repository
If you are studying for core networking exams or cybersecurity certifications, follow the modules in order. Read the theory for a topic, then run the corresponding script to see how the architecture behaves under the hood.

---

### Module 1: The Network Layer (IPv4 Architecture)
*The foundation of internet routing, addressing, and packet manipulation.*
*   **`01_subnet_calculator`**: Processes CIDR notation to calculate strict binary network boundaries, broadcast IDs, and usable host ranges.
*   **`02_vlsm_allocator`**: Dynamically sorts host requirements, calculates powers of 2, and allocates contiguous subnets without overlapping.
*   **`03_route_aggregator`**: Applies Longest Prefix Match (LPM) and alignment rules to fuse multiple contiguous subnets into a Supernet.
*   **`04_ipv4_fragmentation_engine`**: Simulates MTU bottlenecks by calculating header scaling, 8-byte offset rules, and MF bit states for chopped packets.

### Module 2: The Network Layer (ICMP & Routing Algorithms)
*How routers talk to each other and report errors.*
*   **`05_custom_traceroute`**: Manually manipulates the IPv4 TTL (Time to Live) field to force ICMP "Time Exceeded" errors, mapping router hops.
*   **`06_distance_vector_router`**: Implements the Bellman-Ford algorithm (RIP), demonstrating how routing tables converge over time.
*   **`07_link_state_router`**: Implements Dijkstra’s Algorithm (OSPF) to calculate the absolute shortest path tree across a topology.

### Module 3: The Transport Layer (TCP, UDP & Reliability)
*Managing connections, ports, and congestion across the infrastructure.*
*   **`08_tcp_3way_handshake_state_machine`**: Simulates state transitions (LISTEN, SYN_SENT, ESTABLISHED) with randomized sequence numbers.
*   **`09_multithreaded_tcp_server`**: A working socket program where a central server handles multiple concurrent client connections.
*   **`10_udp_rtt_monitor`**: A custom ping utility demonstrating connectionless packet delivery and latency calculations.
*   **`11_tcp_congestion_simulator`**: Visualizes the TCP Congestion Window, simulating Slow Start and Congestion Avoidance algorithms.

### Module 4: The Data Link Layer (Framing & Error Control)
*Surviving the physical wire through bit-level manipulation.*
*   **`12_bit_byte_stuffer`**: Implements framing by algorithmically inserting escape characters or bit sequences to define frame boundaries.
*   **`13_crc_engine`**: Calculates the Cyclic Redundancy Check (CRC) via binary XOR division to verify Ethernet data integrity.
*   **`14_hamming_code_generator`**: Calculates parity bits for Forward Error Correction, capable of detecting and flipping a corrupted bit.
*   **`15_csma_cd_simulator`**: Simulates the Ethernet Exponential Backoff Algorithm for collision domains.
*   **`16_sliding_window_arq`**: Visualizes Stop-and-Wait and Selective Repeat protocols to manage data flow and acknowledgments.

### Module 5: The Physical Layer (Signals)
*Converting binary into physical reality.*
*   **`17_line_coding_simulator`**: Takes binary strings and applies Manchester Encoding and NRZ-I logic to simulate voltage clock synchronization.

### Module 6: Session & Presentation Layers
*Managing user states and data formatting (The absorbed OSI layers).*
*   **`18_session_state_manager`**: Builds a token-based session manager to maintain "state" across a stateless network.
*   **`19_presentation_crypto_engine`**: Serializes, compresses (Huffman coding), and encrypts data payloads before they hit the transport layer.

### Module 7: Application Layer & Security Defense
*Where data interacts with software, and where networks are mapped.*
*   **`20_raw_packet_sniffer`**: Uses raw sockets to bypass the OS, parsing the binary of the 20-byte IPv4 header directly off the network card.
*   **`21_stealth_port_scanner`**: A concurrent diagnostic tool to identify open TCP/UDP ports on target architectures.
*   **`22_dns_resolver_cli`**: Manually constructs a UDP DNS query to extract the A-record (IP address) of a hostname.
*   **`23_http_web_server`**: A lightweight server written purely from raw sockets to parse GET requests and send 200 OK HTML headers.

---
*Built for deep-dive protocol analysis, mathematical engineering, and architectural understanding.*