// Apenas renderização: valores e agregações chegam prontos do servidor.
document.querySelectorAll('script[data-chart]').forEach((source) => {
  const container = document.getElementById(source.dataset.chart);
  const failure = () => {
    container.textContent = 'Não foi possível exibir o gráfico. Consulte as tabelas em Analytics.';
    container.classList.add('notice', 'error');
  };
  try {
    const figure = JSON.parse(source.textContent);
    Plotly.newPlot(container, figure.data, figure.layout, {
      responsive: true, displayModeBar: false, locale: 'pt-BR', scrollZoom: false
    }).then(() => {
      const observer = new ResizeObserver(() => Plotly.Plots.resize(container));
      observer.observe(container.parentElement);
    }).catch(failure);
  } catch (error) {
    failure();
  }
});
