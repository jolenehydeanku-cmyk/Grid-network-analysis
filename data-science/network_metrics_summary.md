# Task 2.1 - Network Metrics Summary

- Total substations (nodes): 44
- Total lines (edges): 55
- Network diameter: 14
- Average shortest path length: 5.41
- Average clustering coefficient: 0.367
- Fully connected: False
- Number of connected components: 3
- Communities detected: 8

## Top 5 Critical Substations (by Betweenness Centrality)

                     Name  Region  Betweenness Centrality
    Cape Coast Substation Central                0.525471
      Takoradi Substation Western                0.516058
Kumasi Central Substation Ashanti                0.500554
     Koforidua Substation Eastern                0.498339
            Ho Substation   Volta                0.436323

## N-1 Contingency Results

               Substation  Components Before  Components After  New Splits Caused  Largest Piece Before  Largest Piece After  Substations Cut Off
    Cape Coast Substation                  3                 5                  2                    42                   20                   22
      Takoradi Substation                  3                 5                  2                    42                   22                   20
Kumasi Central Substation                  3                 6                  3                    42                   26                   16
     Koforidua Substation                  3                 5                  2                    42                   24                   18
            Ho Substation                  3                 5                  2                    42                   28                   14