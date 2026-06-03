# Catalyst Center MCP Open Source

[![Maintainer](https://img.shields.io/badge/Maintainer-Cisco-00bceb.svg)](https://opensource.cisco.com)

## About The Project

This repository contains open source code for the Catalyst Center Open Source MCP Server. 
Each version of Catalyst Center <M.N.P.Q> will have an accompanying branch within this 
repository (release/catc-<M.N.P.Q>) containing the corresponding MCP Server.  

Each MCP server exposes as tools many of the functions exposed as read apis exposed by 
the Catalyst Center.   The context for each tool incorporates the documentation of the 
api endpoint as well as, in some cases, additional context that Cisco believes improves 
the usability of the tool by AI Agents.  

## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

- python 3.12 or above (mandatory)
- A docker build environment (optional)

A dockerfile is included with this release.  Running a docker build provides a standalone 
container able to run the mcp server.  

### Installation

1. Clone the repository

   ```sh
   git clone https://github.com/cisco-en-programmability/catc-mcp-oss
   ```

2. Install npm packages

   ```sh
   npm install
   ```

## Usage

Once you have the MCP Server running, you can request information.  Responses are 
limited only by the public apis available for Catalyst Center to present information. 

Here's an example of a brief interaction: 
```
❯ list my sites

⏺ I'll help you list your sites. Let me load the necessary tool to retrieve sites from
  Catalyst Center.

⏺ Now I'll retrieve your sites from Catalyst Center.

  Called catc (ctrl+o to expand)

⏺ Here are your sites in Catalyst Center:

  Site Hierarchy

  Global (Root)
  - CO (Colorado)
    - ENGL (Englewood) - 9155 East Nichols Avenue, Centennial, CO 80112
        - Floor-5
  - France
    - Paris - 17 Avenue Jules Rimet, 93200 Saint-Denis, France
  - NY (New York)
    - NYC (New York City) - 1 Pennsylvania Plaza, New York, NY 10001
        - Floor-8
  - OR (Oregon)
    - BEAV (Beaverton) - 1600 NW Compton Drive, Beaverton, OR 97006
        - Main
    - LO (Lake Oswego) - 5400 Meadows Rd, Lake Oswego, OR 97035
        - Floor-3
    - PDX (Portland) - 1600 NE Compton Drive, Hillsboro, OR 97006
        - Floor-2
  - SF (San Francisco)
    - SFO - 500 Terry a. François Boulevard, San Francisco, CA 94158
        - Net plat

  Summary: 19 total sites (1 global, 5 areas, 6 buildings, 7 floors)
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Distributed under the Apache License. See [LICENSE](LICENSE) for more
information.

## Contact

Please see [MAINTAINERS.md](MAINTAINERS.md)

Project Link:
[Catalyst Center MCP Open Source](https://github.com/cisco-en-programmability/catc-mcp-oss)

## Acknowledgements

This project is based on work done by the Catalyst Center AI Assistant team. 