# Telegram File Monitor

This project is a Telegram channel monitoring tool that automatically downloads and processes messages from configured channels.

## Features

- **Auto Mode**: Automatically monitors and processes messages from configured channels.
- **Manual Mode**: Allows for manual file processing.
- **Channel Mode**: Focuses on downloading all files from a given channel.
- **Download and Process Workers**: Manages concurrent downloading and processing of messages.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/githubesson/logscraper
    ```

2. Install dependencies:
    ```sh
    sudo apt install ripgrep
    pip3 install -r requirements.txt
    pip3 install readline 
    !! WARNING !! this wont work on windows, and you shouldnt run this project on windows. any issues about this will be closed.
    ```

3. Configure settings:
    - Copy `.env.example` to `.env` and update the configuration values.

## Usage

1. Run the application:
    ```sh
    python3 main.py
    ```

2. Follow the on-screen menu to select the desired mode.

## Configuration

Settings are managed in the `src/config/settings.py` file. Update the configuration values as needed.

## License

This project is licensed under the MIT License.
