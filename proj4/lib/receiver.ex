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
            Basic.consume channel, @queue

            wait_for_messages channel
          {:error, error} ->
            IO.puts "An error occurred while opening channel\n #{error}"
        end
      {:error, error} ->
        IO.puts "An error occurred while opening connection\n #{error}"
    end
  end

  defp wait_for_messages(channel) do
    receive do
      {:basic_deliver, payload, meta} ->
        spawn fn -> consume channel, meta.delivery_tag, meta.redelivered, payload end

        wait_for_messages channel
    end
  end

  defp consume(channel, tag, redelivered, payload) do
    IO.puts "Received message: #{payload}"
    case redelivered do
      false ->
        try do
          Basic.ack channel, tag
        rescue
          _ -> Basic.nack channel, tag, requeue: false
        end
      true ->
        Basic.reject channel, tag, requeue: false
        IO.puts "Rejected message"
    end
    {:ok, channel}
  end

end
