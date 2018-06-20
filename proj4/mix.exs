defmodule Proj4.Mixfile do
  use Mix.Project

  def project do
    [
      app: :proj4,
      version: "0.1.0",
      elixir: "~> 1.5",
      start_permanent: Mix.env == :prod,
      deps: deps()
    ]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do
    [application: [:logger, :amqp]]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:amqp, "~> 0.2.1"}
    ]
  end
end
