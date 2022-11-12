[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/escomputers/BASD">
   <!-- <img src="templates/icon.ico" alt="Logo" width="80" height="80">-->
  </a>

<h3 align="center">BASD</h3>

  <p align="center">
    Binance Automatic Stop Daemon
    <br />
    <br />
    ·
    <a href="https://github.com/escomputers/BASD/issues">Report Bug »</a>
    ·
    <a href="https://github.com/escomputers/BASD/issues">Request Feature »</a>
  </p>
</div>

<!-- WHY BASD -->
## Why BASD?
Binance is unquestionably the world greatest and most secure cryptocurrency exchange and many of us trade there.
For those like me that open and close positions within the same day or few hours, it's extremely important to carefully watch graphs to monitor price movements.

Sometimes (very often in my case) we cannot monitor price during a trade.
Expecially if an order is being filled during nightime, how can we place a Stop Loss, Take Profit or OCO order if we're sleeping, trekking or just working?

BASD solves the problem by constantly and securely listening to Binance account and if a condition is being triggered it will automatically place a Stop Loss, Take Profit or OCO order basing on your choice.


<!-- Prerequisites -->
### Prerequisites
BASD requires <b>Binance.com API key and API secret key</b>. If you don't know how to create API keys, follow these [instructions](https://www.binance.com/en/support/faq/how-to-create-api-360002502072). note that Binance.us is not currently supported.

<!-- GETTING STARTED -->
## Getting started
Just download last stable binary file from [releases](https://github.com/escomputers/BASD/releases) page and run it.

<!-- USAGE -->
## Usage
When program starts you will asked for these <u>required</u> parameters:
* Timezone continent + city <sup>1</sup>
* Start time <sup>2</sup>
* Number of active hours <sup>3</sup>
* Order type <sup>4</sup>
* Sell percentage <sup>5</sup>

<sup>1</sup> [Here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) you can find a complete list of all supported timezones, <b>e.g. Europe/Berlin</b>

<sup>2</sup> When you want program starts working, <b>e.g. 23:55</b>

<sup>3</sup> Number of active hours, used for end time calculation, <b>e.g. 8</b>

<sup>4</sup> Supported order types are <u>only for sell</u> side: [Take Profit](https://academy.binance.com/en/articles/what-is-a-stop-limit-order) - [Stop Loss](https://academy.binance.com/en/articles/what-is-a-stop-limit-order) - [OCO](https://academy.binance.com/en/articles/what-is-an-oco-order)

<sup>5</sup> BASD will calculate order sell price with your desired percentage, <b>e.g. 2.45</b>


### Supported OS
* ![Linux][Linux]
* ![MacOS][MacOS]
* ![Windows][Windows]

<!--
### Installation
1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/escomputers/BASD.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```js
   const API_KEY = 'ENTER YOUR API';
   ```
-->

<!-- CONTRIBUTING -->
## Contributing
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

### If BASD was useful don't forget to give the project a star!


<!-- LICENSE -->
## License
Distributed under the Apache 2.0 License. See [license](https://github.com/escomputers/BASD/blob/GUI/LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/escomputers/BASD.svg?style=for-the-badge
[contributors-url]: https://github.com/escomputers/BASD/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/escomputers/BASD.svg?style=for-the-badge
[forks-url]: https://github.com/escomputers/BASD/network/members
[stars-shield]: https://img.shields.io/github/stars/escomputers/BASD.svg?style=for-the-badge
[stars-url]: https://github.com/escomputers/BASD/stargazers
[issues-shield]: https://img.shields.io/github/issues/escomputers/BASD.svg?style=for-the-badge
[issues-url]: https://github.com/escomputers/BASD/issues
[license-shield]: https://img.shields.io/github/license/escomputers/BASD.svg?style=for-the-badge
[license-url]: https://github.com/escomputers/BASD/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/emiliano-spada/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[HTML]: https://img.shields.io/badge/HTML-239120?style=for-the-badge&logo=html5&logoColor=white
[HTML-url]: https://html.com/
[Linux]: https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black
[MacOS]: https://img.shields.io/badge/mac%20os-000000?style=for-the-badge&logo=macos&logoColor=F0F0F0
[Windows]: https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com