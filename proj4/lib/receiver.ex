defmodule Receiver do
  use GenServer
  use AMQP

  @queue  "distributed_systems"

  def start_link do
    GenServer.start_link(__MODULE__, [], [])
  end

  def init(_opts) do
    rabbitmq_connect()
  end

  defp rabbitmq_connect do
    case Connection.open do
      {:ok, connection} ->
        case Channel.open connection do
          {:ok, channel} ->
            IO.puts "Connected in RabbitMQ."

            Queue.declare channel, @queue, durable: true
            {:ok, _consumer_tag} = Basic.consume channel, @queue
          {:error, error} ->
            IO.puts "An error occurred while opening channel\n #{error}"
        end
      {:error, error} ->
        IO.puts "An error occurred while opening connection\n #{error}"
    end
  end

  def handle_info({:basic_consume_ok, _}, chan) do
    {:noreply, chan}
  end

  def handle_info({:basic_cancel, _}, chan) do
    {:stop, :normal, chan}
  end

  def handle_info({:basic_cancel_ok, _}, chan) do
    {:noreply, chan}
  end

  def handle_info({:basic_deliver, payload, meta}, chan) do
    spawn fn -> consume(chan, meta.delivery_tag, meta.redelivered, payload) end
    {:noreply, chan}
  end

  defp consume(channel, tag, redelivered, payload) do
    IO.puts "Received message: #{payload}"

    try do
      Basic.ack channel, tag
    rescue
      _ ->
        :ok = Basic.reject channel, tag, not redelivered
        IO.puts "Exception in ACK"
    end
  end

end
