document.addEventListener("DOMContentLoaded", function() {
    const temperatureUnitRadios = document.querySelectorAll('input[name="temperature-unit"]');
    const pressureUnitRadios = document.querySelectorAll('input[name="pressure-unit"]');
    const windUnitRadios = document.querySelectorAll('input[name="wind-unit"]');
    const visibilityUnitRadios = document.querySelectorAll('input[name="visibility-unit"]');

    const directionMap = {
        'N': 'bi-arrow-up',
        'NNE': 'bi-arrow-up-right',
        'NE': 'bi-arrow-up-right',
        'ENE': 'bi-arrow-right',
        'E': 'bi-arrow-right',
        'ESE': 'bi-arrow-right',
        'SE': 'bi-arrow-down-right',
        'SSE': 'bi-arrow-down',
        'S': 'bi-arrow-down',
        'SSW': 'bi-arrow-down-left',
        'SW': 'bi-arrow-down-left',
        'WSW': 'bi-arrow-left',
        'W': 'bi-arrow-left',
        'WNW': 'bi-arrow-left',
        'NW': 'bi-arrow-up-left',
        'NNW': 'bi-arrow-up-left'
    };

    temperatureUnitRadios.forEach(radio => radio.addEventListener('change', updateUnits));
    pressureUnitRadios.forEach(radio => radio.addEventListener('change', updateUnits));
    windUnitRadios.forEach(radio => radio.addEventListener('change', updateUnits));
    visibilityUnitRadios.forEach(radio => radio.addEventListener('change', updateUnits));

    function updateUnits() {
        const temperatureUnit = document.querySelector('input[name="temperature-unit"]:checked').value;
        const pressureUnit = document.querySelector('input[name="pressure-unit"]:checked').value;
        const windUnit = document.querySelector('input[name="wind-unit"]:checked').value;
        const visibilityUnit = document.querySelector('input[name="visibility-unit"]:checked').value;

        // Update temperature
        const temperatureElements = document.querySelectorAll('.temp-value, .forecast-temp-value');
        temperatureElements.forEach(el => {
            const tempC = el.getAttribute('data-temp-c');
            const tempF = el.getAttribute('data-temp-f');
            el.innerHTML = (temperatureUnit === 'c') ? `${tempC}<sup class="temp-unit forecast-temp-unit">°C</sup>` : `${tempF}<sup class="temp-unit forecast-temp-unit">°F</sup>`;
        });

        // Update feels like temperature
        const feelslikeElements = document.querySelectorAll('.feelslike');
        feelslikeElements.forEach(el => {
            const feelslikeC = el.getAttribute('data-feelslike-c');
            const feelslikeF = el.getAttribute('data-feelslike-f');
            const transFeelsLike = el.getAttribute('data-trans-feelslike');
            el.textContent = (temperatureUnit === 'c') ? `${transFeelsLike} ${feelslikeC}°C` : `${transFeelsLike} ${feelslikeF}°F`;
        });

        // Update dewpoint temperature
        const dewpointElements = document.querySelectorAll('.dewpoint');
        dewpointElements.forEach(el => {
            const dewpointC = el.getAttribute('data-dewpoint-c');
            const dewpointF = el.getAttribute('data-dewpoint-f');
            el.textContent = (temperatureUnit === 'c') ? `${dewpointC}°C` : `${dewpointF}°F`;
        });

        // Update pressure
        const pressureElements = document.querySelectorAll('.pressure');
        pressureElements.forEach(el => {
            const pressureMMHG = el.getAttribute('data-pressure-mmhg');
            const pressureMB = el.getAttribute('data-pressure-mb');
            const transMMHG = el.getAttribute('data-trans-mmhg');
            const transMB = el.getAttribute('data-trans-mb');
            el.textContent = (pressureUnit === 'mmhg') ? `${pressureMMHG} ${transMMHG}` : `${pressureMB} ${transMB}`;
        });

        // Update wind
        const windElements = document.querySelectorAll('.wind');
        windElements.forEach(el => {
            const windKPH = el.getAttribute('data-wind-kph');
            const windMPS = el.getAttribute('data-wind-mps');
            const windMPH = el.getAttribute('data-wind-mph');
            const windDir = el.getAttribute('data-wind-dir');
            const transMPS = el.getAttribute('data-trans-mps');
            const transKPH = el.getAttribute('data-trans-kph');
            const transMPH = el.getAttribute('data-trans-mph');
            const directionClass = directionMap[windDir] || 'bi-question';
            let value;
            if (windUnit === 'mps') {
                value = `<i class="bi ${directionClass}"></i> ${windMPS} ${transMPS}`;
            } else if (windUnit === 'mph') {
                value = `<i class="bi ${directionClass}"></i> ${windMPH} ${transMPH}`;
            } else {
                value = `<i class="bi ${directionClass}"></i> ${windKPH} ${transKPH}`;
            }
            el.innerHTML = value;
        });

        // Update visibility
        const visibilityElements = document.querySelectorAll('.visibility');
        visibilityElements.forEach(el => {
            const visibilityKM = el.getAttribute('data-visibility-km');
            const visibilityMiles = el.getAttribute('data-visibility-miles');
            const numberMiles = parseInt(visibilityMiles);
            const lang = el.getAttribute('data-lang');
            const visibilityUnitText = getVisibilityUnit(numberMiles, lang);
            el.textContent = (visibilityUnit === 'km') ? `${visibilityKM} ${el.getAttribute('data-trans-km')}` : `${visibilityMiles} ${visibilityUnitText}`;
        });
    }

    // JavaScript function to get the correct visibility unit
    function getVisibilityUnit(number, lang) {
        if (lang === 'uk') {
            if (10 <= number % 100 && number % 100 <= 20) {
                return 'миль';
            }
            const lastDigit = number % 10;
            if (lastDigit === 1) {
                return 'миля';
            } else if (2 <= lastDigit && lastDigit <= 4) {
                return 'милі';
            } else {
                return 'миль';
            }
        } else if (lang === 'en') {
            return number === 1 ? 'mile' : 'miles';
        }
    }

    // Initialize the wind direction arrow on page load
    const windElements = document.querySelectorAll('.wind');
    windElements.forEach(el => {
        const windDir = el.getAttribute('data-wind-dir');
        const directionClass = directionMap[windDir] || 'bi-question';
        el.querySelector('.bi').classList.add(directionClass);
    });
});
